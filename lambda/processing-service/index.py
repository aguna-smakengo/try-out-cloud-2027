import json
import os
import boto3
import logging
import psycopg2
import base64

# Configure Logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# --- CONFIG ---
DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME", "bankdb")
DB_USER = os.environ.get("DB_USER", "bankadmin")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
S3_BUCKET = os.environ.get("S3_BUCKET_NAME")

def _get_db_connection():
    return psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, connect_timeout=5)

def lambda_handler(event, context):
    logger.info("[CONSUMER] Processing SQS records: %d", len(event.get("Records", [])))
    
    conn = None
    try:
        conn = _get_db_connection()
        cur = conn.cursor()
        
        for record in event.get("Records", []):
            try:
                task = json.loads(record["body"])
                task_type = task.get("type")
                username = task.get("username")
                
                logger.info("[TASK] Executing %s for user %s", task_type, username)
                
                # Fetch user data for the task
                cur.execute("SELECT user_id, balance, card_number FROM user_profiles WHERE username = %s", (username,))
                user = cur.fetchone()
                if not user:
                    logger.error("[TASK] User %s not found in database", username)
                    continue
                
                user_id, balance, card_num = user[0], float(user[1]), user[2]

                if task_type == "DEPOSIT":
                    amount = float(task.get("amount", 0))
                    cur.execute("UPDATE user_profiles SET balance = balance + %s WHERE user_id = %s", (amount, user_id))
                    cur.execute("UPDATE user_profiles SET balance = balance - %s WHERE username = 'CENTRAL_BANK'", (amount,))
                    logger.info("[SUCCESS] Deposit of $%s for %s completed", amount, username)

                elif task_type == "TRANSFER":
                    amount = float(task.get("amount", 0))
                    raw_to_card = task.get("to_card", "")
                    to_card = "".join(filter(str.isdigit, raw_to_card)) # Standardize card number
                    
                    if amount > balance:
                        logger.warning("[FAILED] Transfer denied: Insufficient funds for %s", username)
                        continue
                        
                    cur.execute("SELECT user_id FROM user_profiles WHERE card_number = %s", (to_card,))
                    target = cur.fetchone()
                    if not target:
                        logger.warning("[FAILED] Transfer failed: Target card %s not found", to_card)
                        continue
                        
                    cur.execute("UPDATE user_profiles SET balance = balance - %s WHERE user_id = %s", (amount, user_id))
                    cur.execute("UPDATE user_profiles SET balance = balance + %s WHERE user_id = %s", (amount, target[0]))
                    logger.info("[SUCCESS] Transfer of $%s from %s to %s completed", amount, username, to_card)

                elif task_type == "REGISTER_FACE":
                    img_raw = task.get("image_data", "")
                    if "," in img_raw:
                        img_b64 = img_raw.split(",")[1]
                        s3_key = f"faces/{user_id}_ref.jpg"
                        
                        # Upload to S3
                        boto3.client('s3').put_object(Bucket=S3_BUCKET, Key=s3_key, Body=base64.b64decode(img_b64), ContentType='image/jpeg')
                        
                        # Update DB
                        cur.execute("UPDATE user_profiles SET face_image_key = %s WHERE user_id = %s", (s3_key, user_id))
                        logger.info("[SUCCESS] Biometrics linked for %s. S3: %s", username, s3_key)

                conn.commit()
                
            except Exception as e:
                logger.error("[ERROR] Task execution failed: %s", str(e))
                if conn: conn.rollback()

    except Exception as e:
        logger.error("[CRITICAL] Processing Service Error: %s", str(e))
    finally:
        if conn: conn.close()
        
    return {"status": "ok"}
