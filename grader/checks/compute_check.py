import boto3

def check_compute_compliance(lmb, apg):
    points = []
    
    # 1. Lambda Audit
    required_lambdas = [
        ('bank-recognition-auth', 'Authentication Service'),
        ('bank-recognition-ingest', 'Ingestion Pipeline'),
        ('bank-recognition-query', 'Query Microservice'),
        ('bank-recognition-processing', 'SQS Consumer / Worker'),
        ('bank-recognition-interest', 'Automation Task')
    ]
    
    for name, desc in required_lambdas:
        try:
            fn = lmb.get_function(FunctionName=name)
            points.append({
                "Category": "4. Compute & API", "Item": f"Lambda: {name} ({desc})",
                "Status": "PASS", "Score": 10,
                "Expected": "Exist", "Actual": "Found",
                "Feedback": f"Mandatory microservice component"
            })
            
            # Check Runtime
            runtime = fn['Configuration']['Runtime']
            status = "PASS" if runtime == 'python3.12' else "FAIL"
            points.append({
                "Category": "4. Compute & API", "Item": f"Lambda Runtime: {name}",
                "Status": status, "Score": 5 if status == "PASS" else 0,
                "Expected": "python3.12", "Actual": runtime,
                "Feedback": "Consistent runtime requirement"
            })
        except:
            points.append({"Category": "4. Compute & API", "Item": f"Lambda: {name}", "Status": "FAIL", "Score": 0, "Feedback": "Missing function"})

    # 2. API Gateway Audit
    try:
        apis = apg.get_rest_apis()['items']
        br_api = next((a for a in apis if a['name'] == 'bank-recognition-api'), None)
        status = "PASS" if br_api else "FAIL"
        points.append({
            "Category": "4. Compute & API", "Item": "REST API Gateway",
            "Status": status, "Score": 25 if status == "PASS" else 0,
            "Expected": "bank-recognition-api", "Actual": "Found" if br_api else "Missing",
            "Feedback": "Primary ingress for frontend traffic"
        })
    except:
        points.append({"Category": "4. Compute & API", "Item": "API Gateway Audit", "Status": "FAIL", "Score": 0, "Feedback": "Error or no API found"})

    return points
