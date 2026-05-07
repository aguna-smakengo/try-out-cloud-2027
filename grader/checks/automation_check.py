import boto3
import json

def check_automation_compliance(sqs, eb):
    points = []
    try:
        queues = sqs.list_queues(QueueNamePrefix='BankRecognitionQueue')['QueueUrls']
        status = "PASS" if queues else "FAIL"
        points.append({"Category": "8. Automation", "Item": "SQS Queue Existence", "Status": status, "Score": 1 if status == "PASS" else 0, "Feedback": "BankRecognitionQueue"})
        if queues:
            attr = sqs.get_queue_attributes(QueueUrl=queues[0], AttributeNames=['VisibilityTimeout', 'RedrivePolicy'])['Attributes']
            points.append({"Category": "8. Automation", "Item": "SQS Visibility Timeout: 120s", "Status": "PASS" if attr['VisibilityTimeout'] == '120' else "FAIL", "Score": 1 if attr['VisibilityTimeout'] == '120' else 0, "Feedback": f"{attr['VisibilityTimeout']}s"})
            points.append({"Category": "8. Automation", "Item": "SQS DLQ Attached", "Status": "PASS" if 'RedrivePolicy' in attr else "FAIL", "Score": 1 if 'RedrivePolicy' in attr else 0, "Feedback": "Attached" if 'RedrivePolicy' in attr else "Missing"})

        rules = eb.list_rules(NamePrefix='bank-recognition-interest-schedule')['Rules']
        status = "PASS" if rules else "FAIL"
        points.append({"Category": "8. Automation", "Item": "EventBridge Rule Existence", "Status": status, "Score": 1 if status == "PASS" else 0, "Feedback": "bank-recognition-interest-schedule"})
        if rules:
            rule = rules[0]
            points.append({"Category": "8. Automation", "Item": "EB Rule State: ENABLED", "Status": "PASS" if rule['State'] == 'ENABLED' else "FAIL", "Score": 1 if rule['State'] == 'ENABLED' else 0, "Feedback": rule['State']})
            points.append({"Category": "8. Automation", "Item": "EB Schedule: rate(30 days)", "Status": "PASS" if rule['ScheduleExpression'] == 'rate(30 days)' else "FAIL", "Score": 1 if rule['ScheduleExpression'] == 'rate(30 days)' else 0, "Feedback": rule['ScheduleExpression']})
    except:
        points.append({"Category": "8. Automation", "Item": "Automation Audit", "Status": "FAIL", "Score": 0, "Feedback": "Error"})
    return points
