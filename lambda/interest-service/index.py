import json
import os
import logging
import psycopg2
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME", "bankdb")
DB_USER = os.environ.get("DB_USER", "bankadmin")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

# Config: 1% monthly interest
MONTHLY_RATE = 0.01
DAILY_RATE = MONTHLY_RATE / 30

def _get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=5
    )

def lambda_handler(event, context):
    """
    Detailed Interest Calculator (Pro-rata).
    Calculates interest for each user based on how long each deposited 
    amount has been in the system.
    """
    logger.info("[ENTRY] interest-service | Triggered by: %s", event.get("source", "Manual/Lambda Console"))
    
    now = datetime.now(timezone.utc)
    processed_count = 0
    total_interest_applied = 0.0

    try:
        with _get_db_connection() as conn:
            with conn.cursor() as cur:
                # 1. Fetch all users
                cur.execute("SELECT user_id, username, balance FROM user_profiles")
                users = cur.fetchall()

                for user_id, username, current_balance in users:
                    logger.info("[interest-service] Processing user: %s (Current Balance: %s)", username, current_balance)
                    
                    # 2. Get all successful recognitions for this user
                    # We only calculate interest for amounts extracted by the AI
                    cur.execute("""
                        SELECT amount, created_at, image_id 
                        FROM bank_recognitions 
                        WHERE user_id = %s AND status = 'PROCESSED'
                    """, (user_id,))
                    
                    transactions = cur.fetchall()
                    user_total_interest = 0.0

                    for amount_str, created_at, image_id in transactions:
                        try:
                            # Clean amount string (e.g. "$1,200.00" -> 1200.00)
                            clean_amount = float(''.join(c for c in amount_str if c.isdigit() or c == '.')) if amount_str else 0.0
                            
                            # Calculate days in account
                            if created_at.tzinfo is None:
                                created_at = created_at.replace(tzinfo=timezone.utc)
                            
                            days_diff = (now - created_at).days
                            if days_diff < 0: days_diff = 0
                            
                            # Pro-rata interest: Amount * (Rate/30) * Days
                            interest = clean_amount * DAILY_RATE * days_diff
                            user_total_interest += interest
                            
                            logger.debug("   - Entry %s: Amt=%s, Days=%d, Interest=%s", image_id, clean_amount, days_diff, interest)
                        except Exception as e:
                            logger.warning("   - Error calculating interest for entry %s: %s", image_id, str(e))

                    # 3. Apply interest to user's balance
                    if user_total_interest > 0:
                        new_balance = float(current_balance) + user_total_interest
                        cur.execute(
                            "UPDATE user_profiles SET balance = %s WHERE user_id = %s",
                            (new_balance, user_id)
                        )
                        logger.info("   >>> Applied +$%s interest to %s. New Balance: %s", 
                                    round(user_total_interest, 4), username, round(new_balance, 2))
                        
                        total_interest_applied += user_total_interest
                        processed_count += 1
                
                conn.commit()

        return {
            "status": "success",
            "users_processed": processed_count,
            "total_interest_applied": round(total_interest_applied, 4),
            "timestamp": now.isoformat()
        }

    except Exception as e:
        logger.error("[ERROR] interest-service | %s", str(e), exc_info=True)
        return {"status": "error", "message": str(e)}
