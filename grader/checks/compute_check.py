import boto3

def check_compute_compliance(lmb, apg):
    points = []
    required_lambdas = [
        ('bank-recognition-auth', 'python3.12', 256, 20),
        ('bank-recognition-ingest', 'python3.12', 1024, 60),
        ('bank-recognition-query', 'python3.12', 512, 30),
        ('bank-recognition-processing', 'python3.12', 512, 120),
        ('bank-recognition-interest', 'python3.12', 256, 60)
    ]
    for name, runtime, mem, timeout in required_lambdas:
        try:
            fn = lmb.get_function(FunctionName=name)
            conf = fn['Configuration']
            points.append({"Category": f"9. Lambda: {name}", "Item": "Existence", "Status": "PASS", "Score": 1, "Feedback": "Found"})
            points.append({"Category": f"9. Lambda: {name}", "Item": f"Runtime: {runtime}", "Status": "PASS" if conf['Runtime'] == runtime else "FAIL", "Score": 1 if conf['Runtime'] == runtime else 0, "Feedback": conf['Runtime']})
            points.append({"Category": f"9. Lambda: {name}", "Item": f"Memory: {mem}MB", "Status": "PASS" if conf['MemorySize'] == mem else "FAIL", "Score": 1 if conf['MemorySize'] == mem else 0, "Feedback": f"{conf['MemorySize']}MB"})
            points.append({"Category": f"9. Lambda: {name}", "Item": "VPC Integration", "Status": "PASS" if 'VpcConfig' in conf and conf['VpcConfig'].get('VpcId') else "FAIL", "Score": 1 if 'VpcConfig' in conf else 0, "Feedback": "Connected"})
        except:
            points.append({"Category": f"9. Lambda: {name}", "Item": "Existence", "Status": "FAIL", "Score": 0, "Feedback": "Not found"})

    try:
        apis = apg.get_rest_apis()['items']
        br_api = next((a for a in apis if a['name'] == 'bank-recognition-api'), None)
        if br_api:
            api_id = br_api['id']
            points.append({"Category": "10. API Gateway", "Item": "API Existence", "Status": "PASS", "Score": 1, "Feedback": "bank-recognition-api"})
            points.append({"Category": "10. API Gateway", "Item": "Endpoint Type: REGIONAL", "Status": "PASS" if 'REGIONAL' in br_api['endpointConfiguration']['types'] else "FAIL", "Score": 1 if 'REGIONAL' in br_api['endpointConfiguration']['types'] else 0, "Feedback": "Regional"})
            resources = apg.get_resources(restApiId=api_id)['items']
            for path in ['/auth', '/ingest', '/query']:
                res = next((r for r in resources if r['path'] == path), None)
                status = "PASS" if res else "FAIL"
                points.append({"Category": f"10. API Resource: {path}", "Item": "Existence", "Status": status, "Score": 1 if status == "PASS" else 0, "Feedback": "Found" if res else "Missing"})
                if res:
                    has_post = 'POST' in res.get('resourceMethods', {})
                    points.append({"Category": f"10. API Resource: {path}", "Item": "Method: POST", "Status": "PASS" if has_post else "FAIL", "Score": 1 if has_post else 0, "Feedback": "Configured"})
        else:
            points.append({"Category": "10. API Gateway", "Item": "API Existence", "Status": "FAIL", "Score": 0, "Feedback": "Missing"})
    except:
        points.append({"Category": "10. API Gateway", "Item": "API Audit", "Status": "FAIL", "Score": 0, "Feedback": "Error"})
    return points
