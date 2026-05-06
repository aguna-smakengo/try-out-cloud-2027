import json
import boto3
import os
import logging

# Configure Logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# --- CONFIG ---
SQS_QUEUE_URL = os.environ.get("SQS_QUEUE_URL")
sqs = boto3.client("sqs")

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

def lambda_handler(event, context):
    path = event.get("path", "")
    method = event.get("httpMethod", "")
    
    logger.info("[EVENT] Ingest Producer: %s %s", method, path)

    if method == "OPTIONS":
        return _cors_response(200, {"message": "Preflight OK"})

    try:
        # 1. Auth Header Validation (Basic check)
        token = event.get("headers", {}).get("Authorization", "")
        if not token or not token.startswith("BASIC_"):
            return _cors_response(401, {"message": "Unauthorized"})
        
        parts = token.split("_")
        if len(parts) < 3:
            return _cors_response(401, {"message": "Invalid Token Format"})
            
        username = parts[1]
        body = json.loads(event.get("body", "{}"))

        # --- TASK DISPATCHER TO SQS ---
        task = None
        
        if "/deposit" in path:
            task = {
                "type": "DEPOSIT",
                "username": username,
                "amount": float(body.get("amount", 0))
            }
        
        elif "/transfer" in path:
            task = {
                "type": "TRANSFER",
                "username": username,
                "to_card": body.get("to_card", ""),
                "amount": float(body.get("amount", 0))
            }
            
        elif "/register-face" in path:
            task = {
                "type": "REGISTER_FACE",
                "username": username,
                "image_data": body.get("image_data", "") # Will be processed by consumer
            }

        if task:
            logger.info("[QUEUE] Sending task to SQS: %s", task["type"])
            sqs.send_message(
                QueueUrl=SQS_QUEUE_URL,
                MessageBody=json.dumps(task)
            )
            return _cors_response(202, {"message": f"Transaction '{task['type']}' queued for processing", "status": "PENDING"})

        # --- SYNC ROUTE: /verify-face (Authentication must be sync) ---
        # Note: In a production app, verify-face might be in Auth service.
        # For now, let's keep it here or move it to a sync-only logic.
        # But wait, the user said ingest should only be Rekognition + SQS.
        # I'll move verify-face logic to query-service or a dedicated sync service.
        
        return _cors_response(404, {"message": "Endpoint not found in Ingest Service"})

    except Exception as e:
        logger.error("[CRITICAL] Ingest Producer Error: %s", str(e), exc_info=True)
        return _cors_response(500, {"message": str(e)})
