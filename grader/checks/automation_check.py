import boto3
import json

def check_automation_compliance(sqs, eb):
    points = []
    try:
        queues = sqs.list_queues(QueueNamePrefix='BankRecognitionQueue')['QueueUrls']
        exists = "PASS" if queues else "FAIL"
        points.append({
            "Category": "8. Automation", "Item": "SQS Queue Existence", 
            "Status": exists, "Score": 1 if exists == "PASS" else 0, 
            "Expected": "BankRecognitionQueue", "Actual": "Found" if queues else "Missing",
            "Feedback": "Messaging bus presence"
        })
        if queues:
            attr = sqs.get_queue_attributes(QueueUrl=queues[0], AttributeNames=['VisibilityTimeout', 'RedrivePolicy'])['Attributes']
            vt = attr.get('VisibilityTimeout', 'N/A')
            points.append({
                "Category": "8. Automation", "Item": "SQS Visibility Timeout: 120s", 
                "Status": "PASS" if vt == '120' else "FAIL", "Score": 1 if vt == '120' else 0, 
                "Expected": "120s", "Actual": f"{vt}s",
                "Feedback": "Processing window"
            })
            dlq = 'RedrivePolicy' in attr
            points.append({
                "Category": "8. Automation", "Item": "SQS DLQ Attached", 
                "Status": "PASS" if dlq else "FAIL", "Score": 1 if dlq else 0, 
                "Expected": "Attached", "Actual": "Verified" if dlq else "Missing",
                "Feedback": "Error handling queue"
            })

        rules = eb.list_rules(NamePrefix='bank-recognition-interest-schedule')['Rules']
        exists = "PASS" if rules else "FAIL"
        points.append({
            "Category": "8. Automation", "Item": "EventBridge Rule Existence", 
            "Status": exists, "Score": 1 if exists == "PASS" else 0, 
            "Expected": "bank-recognition-interest-schedule", "Actual": "Found" if rules else "Missing",
            "Feedback": "Task scheduler presence"
        })
        if rules:
            rule = rules[0]
            points.append({
                "Category": "8. Automation", "Item": "EB Rule State: ENABLED", 
                "Status": "PASS" if rule['State'] == 'ENABLED' else "FAIL", "Score": 1 if rule['State'] == 'ENABLED' else 0, 
                "Expected": "ENABLED", "Actual": rule['State'],
                "Feedback": "Active schedule status"
            })
            points.append({
                "Category": "8. Automation", "Item": "EB Schedule: rate(30 days)", 
                "Status": "PASS" if rule['ScheduleExpression'] == 'rate(30 days)' else "FAIL", "Score": 1 if rule['ScheduleExpression'] == 'rate(30 days)' else 0, 
                "Expected": "rate(30 days)", "Actual": rule['ScheduleExpression'],
                "Feedback": "Interval validation"
            })
    except:
        points.append({"Category": "8. Automation", "Item": "Automation Audit", "Status": "FAIL", "Score": 0, "Expected": "Success", "Actual": "Error", "Feedback": "Discovery failed"})
    return points
