import boto3

def check_compute_compliance(lmb, apg):
    points = []
    
    # --- 1. LAMBDA INSANE AUDIT ---
    # (Name, Handler, Runtime, Memory, Timeout)
    required_lambdas = [
        ('bank-recognition-auth', 'index.lambda_handler', 'python3.12', 256, 20),
        ('bank-recognition-ingest', 'index.lambda_handler', 'python3.12', 1024, 60),
        ('bank-recognition-query', 'index.lambda_handler', 'python3.12', 512, 30),
        ('bank-recognition-processing', 'index.lambda_handler', 'python3.12', 512, 120),
        ('bank-recognition-interest', 'index.lambda_handler', 'python3.12', 256, 60)
    ]
    
    for name, handler, runtime, mem, timeout in required_lambdas:
        try:
            fn = lmb.get_function(FunctionName=name)
            conf = fn['Configuration']
            
            points.append({"Category": f"7. Lambda: {name}", "Item": "Create/Existence", "Status": "PASS", "Score": 1, "Feedback": "Found"})
            points.append({"Category": f"7. Lambda: {name}", "Item": "Name Compliance", "Status": "PASS", "Score": 1, "Feedback": name})
            points.append({"Category": f"7. Lambda: {name}", "Item": f"Runtime: {runtime}", "Status": "PASS" if conf['Runtime'] == runtime else "FAIL", "Score": 1, "Feedback": conf['Runtime']})
            points.append({"Category": f"7. Lambda: {name}", "Item": f"Memory: {mem}MB", "Status": "PASS" if conf['MemorySize'] == mem else "FAIL", "Score": 1, "Feedback": f"{conf['MemorySize']}MB"})
            points.append({"Category": f"7. Lambda: {name}", "Item": f"Timeout: {timeout}s", "Status": "PASS" if conf['Timeout'] == timeout else "FAIL", "Score": 1, "Feedback": f"{conf['Timeout']}s"})
            points.append({"Category": f"7. Lambda: {name}", "Item": "VPC Networking", "Status": "PASS" if 'VpcConfig' in conf and conf['VpcConfig'].get('VpcId') else "FAIL", "Score": 1, "Feedback": "Connected"})
            
            # Layer Check (1 pt) for specific ones
            if name in ['bank-recognition-auth', 'bank-recognition-query', 'bank-recognition-processing', 'bank-recognition-interest']:
                has_layers = len(conf.get('Layers', [])) > 0
                points.append({"Category": f"7. Lambda: {name}", "Item": "Psycopg2 Layer Attached", "Status": "PASS" if has_layers else "FAIL", "Score": 1, "Feedback": "Attached" if has_layers else "Missing"})
        except:
            points.append({"Category": f"7. Lambda: {name}", "Item": "Existence", "Status": "FAIL", "Score": 0, "Feedback": "Not found"})

    # --- 2. API GATEWAY INSANE AUDIT ---
    try:
        apis = apg.get_rest_apis()['items']
        br_api = next((a for a in apis if a['name'] == 'bank-recognition-api'), None)
        
        if br_api:
            api_id = br_api['id']
            points.append({"Category": "8. API Gateway", "Item": "API: Create/Existence", "Status": "PASS", "Score": 1, "Feedback": "bank-recognition-api"})
            points.append({"Category": "8. API Gateway", "Item": "API: Name Compliance", "Status": "PASS", "Score": 1, "Feedback": "bank-recognition-api"})
            points.append({"Category": "8. API Gateway", "Item": "Endpoint Type: Regional", "Status": "PASS" if 'REGIONAL' in br_api['endpointConfiguration']['types'] else "FAIL", "Score": 1, "Feedback": "Regional"})
            
            # Deep Resource/Method Check
            resources = apg.get_resources(restApiId=api_id)['items']
            for path in ['/auth', '/ingest', '/query']:
                res = next((r for r in resources if r['path'] == path), None)
                r_status = "PASS" if res else "FAIL"
                points.append({"Category": f"8. API Resource: {path}", "Item": "Resource Existence", "Status": r_status, "Score": 1 if r_status == "PASS" else 0, "Feedback": "Found" if res else "Missing"})
                
                if res:
                    methods = res.get('resourceMethods', {})
                    has_post = 'POST' in methods
                    points.append({"Category": f"8. API Resource: {path}", "Item": "Method: POST", "Status": "PASS" if has_post else "FAIL", "Score": 1 if has_post else 0, "Feedback": "Configured" if has_post else "Missing"})
                    
                    if has_post:
                        # Integration Check (1 pt)
                        integration = apg.get_integration(restApiId=api_id, resourceId=res['id'], httpMethod='POST')
                        is_proxy = integration['type'] == 'AWS_PROXY'
                        points.append({"Category": f"8. API Resource: {path}", "Item": "Integration: Lambda Proxy", "Status": "PASS" if is_proxy else "FAIL", "Score": 1, "Feedback": integration['type']})
        else:
            points.append({"Category": "8. API Gateway", "Item": "API Gateway Audit", "Status": "FAIL", "Score": 0, "Feedback": "Missing"})
    except:
        points.append({"Category": "8. API Gateway", "Item": "API Gateway Audit", "Status": "FAIL", "Score": 0, "Feedback": "Failed"})

    return points
