import boto3

def check_automation_compliance(sqs, eb):
    points = []
    
    # 1. SQS Audit
    try:
        queues = sqs.list_queues(QueueNamePrefix='BankRecognitionQueue')['QueueUrls']
        status = "PASS" if queues else "FAIL"
        points.append({
            "Category": "6. Automation", "Item": "SQS Queue Existence",
            "Status": status, "Score": 25 if status == "PASS" else 0,
            "Expected": "BankRecognitionQueue", "Actual": "Found" if queues else "Missing",
            "Feedback": "Async transaction pipeline must exist"
        })
    except:
        points.append({"Category": "6. Automation", "Item": "SQS Audit Error", "Status": "FAIL", "Score": 0, "Feedback": "Error during discovery"})

    # 2. EventBridge Audit
    try:
        rules = eb.list_rules(NamePrefix='bank-recognition-interest-schedule')['Rules']
        status = "PASS" if rules else "FAIL"
        points.append({
            "Category": "6. Automation", "Item": "EventBridge Rule",
            "Status": status, "Score": 15 if status == "PASS" else 0,
            "Expected": "bank-recognition-interest-schedule", "Actual": "Found" if rules else "Missing",
            "Feedback": "Automation heartbeat for interest calculation"
        })
        
        if rules:
            expr = rules[0]['ScheduleExpression']
            status = "PASS" if expr == 'rate(30 days)' else "FAIL"
            points.append({
                "Category": "6. Automation", "Item": "EventBridge Schedule Frequency",
                "Status": status, "Score": 10 if status == "PASS" else 0,
                "Expected": "rate(30 days)", "Actual": expr,
                "Feedback": "Schedule must follow the 30-day billing cycle"
            })
    except:
        points.append({"Category": "6. Automation", "Item": "EventBridge Audit Error", "Status": "FAIL", "Score": 0, "Feedback": "Error during discovery"})

    return points
