import boto3

def check_compute_compliance(lmb, apg):
    points = []
    
    # 1. Lambda Micro-Audit
    required_lambdas = [
        ('bank-recognition-auth', 'index.lambda_handler', 'python3.12'),
        ('bank-recognition-ingest', 'index.lambda_handler', 'python3.12'),
        ('bank-recognition-query', 'index.lambda_handler', 'python3.12'),
        ('bank-recognition-processing', 'index.lambda_handler', 'python3.12'),
        ('bank-recognition-interest', 'index.lambda_handler', 'python3.12')
    ]
    
    for name, handler, runtime in required_lambdas:
        try:
            fn = lmb.get_function(FunctionName=name)
            conf = fn['Configuration']
            
            # Existence (1 pt)
            points.append({"Category": "4. Compute", "Item": f"Lambda {name}: Existence", "Status": "PASS", "Score": 1, "Feedback": "Found"})
            # Naming Compliance (1 pt)
            points.append({"Category": "4. Compute", "Item": f"Lambda {name}: Naming Standard", "Status": "PASS", "Score": 1, "Feedback": "Prefix bank-recognition- confirmed"})
            # Runtime (1 pt)
            status = "PASS" if conf['Runtime'] == runtime else "FAIL"
            points.append({"Category": "4. Compute", "Item": f"Lambda {name}: Runtime Config", "Status": status, "Score": 1 if status == "PASS" else 0, "Expected": runtime, "Actual": conf['Runtime'], "Feedback": "Correct python version"})
            # Handler (1 pt)
            status = "PASS" if conf['Handler'] == handler else "FAIL"
            points.append({"Category": "4. Compute", "Item": f"Lambda {name}: Handler Config", "Status": status, "Score": 1 if status == "PASS" else 0, "Expected": handler, "Actual": conf['Handler'], "Feedback": "Correct entry point"})
            # VPC Config (1 pt)
            vpc_ok = 'VpcConfig' in conf and conf['VpcConfig'].get('VpcId')
            points.append({"Category": "4. Compute", "Item": f"Lambda {name}: VPC Integration", "Status": "PASS" if vpc_ok else "FAIL", "Score": 1 if vpc_ok else 0, "Feedback": "Connected to VPC"})
            
        except:
            points.append({"Category": "4. Compute", "Item": f"Lambda {name}", "Status": "FAIL", "Score": 0, "Feedback": "Resource missing"})

    # 2. API Gateway Micro-Audit
    try:
        apis = apg.get_rest_apis()['items']
        br_api = next((a for a in apis if a['name'] == 'bank-recognition-api'), None)
        
        if br_api:
            api_id = br_api['id']
            points.append({"Category": "4. API Gateway", "Item": "API Name Compliance", "Status": "PASS", "Score": 1, "Feedback": "bank-recognition-api"})
            points.append({"Category": "4. API Gateway", "Item": "API Type: Regional", "Status": "PASS" if 'REGIONAL' in br_api['endpointConfiguration']['types'] else "FAIL", "Score": 1, "Feedback": "Regional endpoint"})
            
            # Check Resources
            resources = apg.get_resources(restApiId=api_id)['items']
            paths = [r['path'] for r in resources]
            for target_path in ['/auth', '/ingest', '/query']:
                status = "PASS" if target_path in paths else "FAIL"
                points.append({"Category": "4. API Gateway", "Item": f"Endpoint Resource: {target_path}", "Status": status, "Score": 1 if status == "PASS" else 0, "Feedback": f"Path {target_path} exists"})
                
                if status == "PASS":
                    res_id = next(r['id'] for r in resources if r['path'] == target_path)
                    res_detail = apg.get_resource(restApiId=api_id, resourceId=res_id)
                    has_post = 'POST' in res_detail.get('resourceMethods', {})
                    points.append({"Category": "4. API Gateway", "Item": f"Endpoint Method: {target_path} POST", "Status": "PASS" if has_post else "FAIL", "Score": 1 if has_post else 0, "Feedback": "POST method configured"})
        else:
            points.append({"Category": "4. API Gateway", "Item": "API Gateway Existence", "Status": "FAIL", "Score": 0, "Feedback": "bank-recognition-api missing"})
    except:
        points.append({"Category": "4. API Gateway", "Item": "API Audit Error", "Status": "FAIL", "Score": 0, "Feedback": "Discovery failed"})

    return points
