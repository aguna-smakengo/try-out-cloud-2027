import boto3

def check_automation_compliance(sqs, eb):
    points = []
    
    # 1. SQS Micro-Audit
    try:
        queues = sqs.list_queues(QueueNamePrefix='BankRecognitionQueue')['QueueUrls']
        exists = "PASS" if queues else "FAIL"
        points.append({"Category": "6. Automation", "Item": "SQS Queue Existence", "Status": exists, "Score": 1 if exists == "PASS" else 0, "Feedback": "BankRecognitionQueue"})
        if queues:
            attr = sqs.get_queue_attributes(QueueUrl=queues[0], AttributeNames=['VisibilityTimeout'])['Attributes']
            points.append({"Category": "6. Automation", "Item": "SQS Visibility Timeout", "Status": "PASS", "Score": 1, "Feedback": f"{attr['VisibilityTimeout']}s"})
    except:
        points.append({"Category": "6. Automation", "Item": "SQS Audit", "Status": "FAIL", "Score": 0, "Feedback": "Failed"})

    # 2. EventBridge Micro-Audit
    try:
        rules = eb.list_rules(NamePrefix='bank-recognition-interest-schedule')['Rules']
        exists = "PASS" if rules else "FAIL"
        points.append({"Category": "6. Automation", "Item": "EventBridge Rule Existence", "Status": exists, "Score": 1 if exists == "PASS" else 0, "Feedback": "bank-recognition-interest-schedule"})
        if rules:
            rule = rules[0]
            # State (1 pt)
            points.append({"Category": "6. Automation", "Item": "EB Rule State: ENABLED", "Status": "PASS" if rule['State'] == 'ENABLED' else "FAIL", "Score": 1, "Feedback": rule['State']})
            # Schedule (1 pt)
            status = "PASS" if rule['ScheduleExpression'] == 'rate(30 days)' else "FAIL"
            points.append({"Category": "6. Automation", "Item": "EB Schedule: rate(30 days)", "Status": status, "Score": 1 if status == "PASS" else 0, "Feedback": rule['ScheduleExpression']})
    except:
        points.append({"Category": "6. Automation", "Item": "EventBridge Audit", "Status": "FAIL", "Score": 0, "Feedback": "Failed"})

    return points
