import boto3
import json

def check_automation_compliance(sqs, eb):
    points = []
    
    # --- 1. SQS INSANE AUDIT ---
    try:
        queues = sqs.list_queues(QueueNamePrefix='BankRecognitionQueue')['QueueUrls']
        exists = "PASS" if queues else "FAIL"
        points.append({"Category": "9. SQS Messaging", "Item": "Queue: Create/Existence", "Status": exists, "Score": 1 if exists == "PASS" else 0, "Feedback": "BankRecognitionQueue"})
        
        if queues:
            q_url = queues[0]
            attr = sqs.get_queue_attributes(QueueUrl=q_url, AttributeNames=['VisibilityTimeout', 'RedrivePolicy'])['Attributes']
            
            points.append({"Category": "9. SQS Messaging", "Item": "Queue: Name Compliance", "Status": "PASS", "Score": 1, "Feedback": "BankRecognitionQueue"})
            points.append({"Category": "9. SQS Messaging", "Item": "Config: VisibilityTimeout (120s)", "Status": "PASS" if attr['VisibilityTimeout'] == '120' else "FAIL", "Score": 1, "Feedback": f"{attr['VisibilityTimeout']}s"})
            
            # DLQ Check (1 pt)
            has_dlq = 'RedrivePolicy' in attr
            points.append({"Category": "9. SQS Messaging", "Item": "Config: Dead Letter Queue (DLQ)", "Status": "PASS" if has_dlq else "FAIL", "Score": 1, "Feedback": "Attached" if has_dlq else "Missing"})
            
            if has_dlq:
                rp = json.loads(attr['RedrivePolicy'])
                points.append({"Category": "9. SQS Messaging", "Item": "DLQ: MaxReceiveCount (3)", "Status": "PASS" if rp['maxReceiveCount'] == 3 else "FAIL", "Score": 1, "Feedback": str(rp['maxReceiveCount'])})

        # Separate DLQ Check
        dlqs = sqs.list_queues(QueueNamePrefix='BankRecognitionDLQ')['QueueUrls']
        points.append({"Category": "9. SQS Messaging", "Item": "DLQ: Create/Existence", "Status": "PASS" if dlqs else "FAIL", "Score": 1, "Feedback": "BankRecognitionDLQ"})
    except:
        points.append({"Category": "9. SQS Messaging", "Item": "SQS Audit", "Status": "FAIL", "Score": 0, "Feedback": "Failed"})

    # --- 2. EVENTBRIDGE INSANE AUDIT ---
    try:
        rules = eb.list_rules(NamePrefix='bank-recognition-interest-schedule')['Rules']
        exists = "PASS" if rules else "FAIL"
        points.append({"Category": "10. EventBridge", "Item": "Rule: Create/Existence", "Status": exists, "Score": 1 if exists == "PASS" else 0, "Feedback": "bank-recognition-interest-schedule"})
        
        if rules:
            rule = rules[0]
            points.append({"Category": "10. EventBridge", "Item": "Rule: Name Compliance", "Status": "PASS", "Score": 1, "Feedback": rule['Name']})
            points.append({"Category": "10. EventBridge", "Item": "Rule: State (ENABLED)", "Status": "PASS" if rule['State'] == 'ENABLED' else "FAIL", "Score": 1, "Feedback": rule['State']})
            points.append({"Category": "10. EventBridge", "Item": "Schedule: rate(30 days)", "Status": "PASS" if rule['ScheduleExpression'] == 'rate(30 days)' else "FAIL", "Score": 1, "Feedback": rule['ScheduleExpression']})
    except:
        points.append({"Category": "10. EventBridge", "Item": "EventBridge Audit", "Status": "FAIL", "Score": 0, "Feedback": "Failed"})

    return points
