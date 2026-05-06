import json
import os
import logging
import psycopg2

# Configure Logging
logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME", "bankdb")
DB_USER = os.environ.get("DB_USER", "bankadmin")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

def _get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=5
    )

def _cors_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET"
        },
        "body": json.dumps(body)
    }

def _ensure_user_table(cursor):
    """Ensures the user_profiles table exists and performs auto-migrations."""
    logger.info("[DB] Verifying database schema and system accounts...")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            pin VARCHAR(6) NOT NULL,
            face_image_key VARCHAR(255),
            balance DECIMAL(15, 2) DEFAULT 0.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Auto-Migration for card_number
    cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='user_profiles' AND column_name='card_number'")
    if not cursor.fetchone():
        logger.info("[MIGRATION] Adding 'card_number' column to user_profiles")
        cursor.execute("ALTER TABLE user_profiles ADD COLUMN card_number VARCHAR(19) UNIQUE")
        cursor.execute("UPDATE user_profiles SET card_number = '0000000000000000' WHERE card_number IS NULL")
        cursor.execute("ALTER TABLE user_profiles ALTER COLUMN card_number SET NOT NULL")
    
    # Auto-clean existing card numbers (remove spaces)
    logger.info("[MIGRATION] Normalizing card numbers (stripping spaces)")
    cursor.execute("UPDATE user_profiles SET card_number = REPLACE(card_number, ' ', '')")

    # Seed Central Bank
    cursor.execute("SELECT user_id FROM user_profiles WHERE username = 'CENTRAL_BANK'")
    if not cursor.fetchone():
        logger.info("[SEED] Creating CENTRAL_BANK system account")
        cursor.execute(
            "INSERT INTO user_profiles (username, pin, card_number, balance) VALUES (%s, %s, %s, %s)",
            ("CENTRAL_BANK", "000000", "0000000000000000", 1000000000.00)
        )
    
    # Seed Master Admin
    cursor.execute("SELECT user_id FROM user_profiles WHERE username = 'master_admin'")
    if not cursor.fetchone():
        logger.info("[SEED] Creating master_admin test account")
        cursor.execute(
            "INSERT INTO user_profiles (username, pin, card_number, balance) VALUES (%s, %s, %s, %s)",
            ("master_admin", "123456", "1111222233334444", 500000.00)
        )

def _generate_card_number(cursor):
    import random
    while True:
        digits = "".join([str(random.randint(0, 9)) for _ in range(16)])
        card_num = " ".join([digits[i:i+4] for i in range(0, 16, 4)])
        cursor.execute("SELECT user_id FROM user_profiles WHERE card_number = %s", (card_num,))
        if not cursor.fetchone():
            return card_num

def lambda_handler(event, context):
    path = event.get("path", "")
    method = event.get("httpMethod", "")
    
    logger.info("[EVENT] Incoming Request: %s %s", method, path)

    if method == "OPTIONS":
        return _cors_response(200, {"message": "Preflight OK"})

    try:
        body = json.loads(event.get("body", "{}"))
        
        with _get_db_connection() as conn:
            with conn.cursor() as cur:
                _ensure_user_table(cur)
                
                # --- ROUTE: /register ---
                if "/register" in path:
                    username = body.get("username")
                    pin = body.get("pin")
                    logger.info("[AUTH] Attempting registration for: %s", username)
                    
                    try:
                        card_num = _generate_card_number(cur)
                        cur.execute(
                            "INSERT INTO user_profiles (username, pin, card_number) VALUES (%s, %s, %s) RETURNING user_id", 
                            (username, pin, card_num)
                        )
                        user_id = cur.fetchone()[0]
                        conn.commit()
                        
                        logger.info("[AUTH] Registration successful. ID: %s | Card: %s", user_id, card_num)
                        return _cors_response(201, {
                            "status": "success", 
                            "user": {"id": user_id, "username": username, "balance": 0.0, "card_number": card_num},
                            "token": f"BASIC_{username}_{pin}"
                        })
                    except psycopg2.errors.UniqueViolation:
                        conn.rollback()
                        logger.warning("[AUTH] Registration failed: Username %s already exists", username)
                        return _cors_response(409, {"message": f"Access Identifier '{username}' is already taken. Please choose another."})

                # --- ROUTE: /login ---
                elif "/login" in path:
                    username = body.get("username")
                    logger.info("[AUTH] Attempting login for: %s", username)
                    
                    cur.execute(
                        "SELECT user_id, username, balance, card_number, face_image_key FROM user_profiles WHERE username = %s AND pin = %s",
                        (username, body.get("pin"))
                    )
                    user = cur.fetchone()
                    if user:
                        logger.info("[AUTH] Login successful for: %s | Biometrics: %s", username, "Registered" if user[4] else "Pending")
                        return _cors_response(200, {
                            "status": "success", 
                            "user": {
                                "id": user[0],
                                "username": user[1],
                                "balance": float(user[2]),
                                "card_number": user[3],
                                "face_image_key": user[4]
                            },
                            "token": f"BASIC_{username}_{body.get('pin')}"
                        })
                    
                    logger.warning("[AUTH] Login failed: Invalid credentials for %s", username)
                    return _cors_response(401, {"message": "Invalid username or PIN"})

        return _cors_response(404, {"message": "Route not found"})

    except Exception as e:
        logger.error("[CRITICAL] Auth Service Error: %s", str(e), exc_info=True)
        return _cors_response(500, {"message": str(e)})
