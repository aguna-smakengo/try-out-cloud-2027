import json
import boto3
import os
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

def _cors_response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }

def _get_db_connection():
    return psycopg2.connect(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, connect_timeout=5)

def lambda_handler(event, context):
    path = event.get("path", "")
    method = event.get("httpMethod", "")
    
    logger.info("[QUERY] Request: %s %s", method, path)

    if method == "OPTIONS":
        return _cors_response(200, {"message": "Preflight OK"})

    conn = None
    try:
        # Auth Check
        token = event.get("headers", {}).get("Authorization", "")
        if not token or not token.startswith("BASIC_"):
            return _cors_response(401, {"message": "Unauthorized"})
        
        parts = token.split("_")
        username, pin = parts[1], parts[2]

        conn = _get_db_connection()
        cur = conn.cursor()
        
        # Verify user
        cur.execute("SELECT user_id, username, balance, card_number, face_image_key FROM user_profiles WHERE username = %s AND pin = %s", (username, pin))
        user_row = cur.fetchone()
        if not user_row:
            return _cors_response(403, {"message": "Forbidden"})
            
        user_id, username, balance, card_number, face_key = user_row[0], user_row[1], float(user_row[2]), user_row[3], user_row[4]

        # --- ROUTE: /me (Get User Profile) ---
        if "/me" in path or "/profile" in path:
            return _cors_response(200, {
                "status": "success",
                "user": {
                    "id": user_id,
                    "username": username,
                    "balance": balance,
                    "card_number": card_number,
                    "face_image_key": face_key
                }
            })

        # --- ROUTE: /verify-face (Sync Biometric Auth) ---
        elif "/verify-face" in path:
            if not face_key:
                return _cors_response(400, {"message": "No face registered"})
                
            body = json.loads(event.get("body", "{}"))
            img_raw = body.get("image_data", "")
            if "," not in img_raw:
                return _cors_response(400, {"message": "Invalid image format"})
            
            img_b64 = img_raw.split(",")[1]
            
            # Download reference from S3
            s3 = boto3.client('s3')
            ref_obj = s3.get_object(Bucket=S3_BUCKET, Key=face_key)
            ref_bytes = ref_obj['Body'].read()
            
            # Compare
            rek = boto3.client('rekognition')
            resp = rek.compare_faces(
                SourceImage={'Bytes': ref_bytes},
                TargetImage={'Bytes': base64.b64decode(img_b64)},
                SimilarityThreshold=85
            )
            verified = len(resp['FaceMatches']) > 0
            return _cors_response(200, {"verified": verified})

        return _cors_response(404, {"message": "Query endpoint not found"})

    except Exception as e:
        logger.error("[ERROR] Query Service Error: %s", str(e))
        return _cors_response(500, {"message": str(e)})
    finally:
        if conn: conn.close()
