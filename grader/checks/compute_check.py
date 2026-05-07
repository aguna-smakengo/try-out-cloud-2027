import boto3

def check_compute_compliance(lmb, apg):
    points = []
    
    # Configuration Standards
    required_lambdas = [
        # (Name, Runtime, Memory, Timeout, Handler)
        ('bank-recognition-auth', 'python3.12', 256, 20, 'index.lambda_handler'),
        ('bank-recognition-ingest', 'python3.12', 1024, 60, 'index.lambda_handler'),
        ('bank-recognition-query', 'python3.12', 512, 30, 'index.lambda_handler'),
        ('bank-recognition-processing', 'python3.12', 512, 120, 'index.lambda_handler'),
        ('bank-recognition-interest', 'python3.12', 256, 60, 'index.lambda_handler')
    ]
    
    for name, runtime, mem, timeout, handler in required_lambdas:
        conf = None
        try:
            fn = lmb.get_function(FunctionName=name)
            conf = fn['Configuration']
        except:
            pass

        # 1. Existence Point
        status = "PASS" if conf else "FAIL"
        points.append({"Category": f"9. Lambda: {name}", "Item": "Existence", "Status": status, "Score": 1 if status == "PASS" else 0, "Feedback": "Found" if conf else "Resource Missing"})
        
        # 2. Runtime Point
        status = "PASS" if conf and conf.get('Runtime') == runtime else "FAIL"
        points.append({"Category": f"9. Lambda: {name}", "Item": f"Runtime: {runtime}", "Status": status, "Score": 1 if status == "PASS" else 0, "Feedback": conf.get('Runtime', 'N/A') if conf else "N/A"})
        
        # 3. Memory Point
        status = "PASS" if conf and conf.get('MemorySize') == mem else "FAIL"
        points.append({"Category": f"9. Lambda: {name}", "Item": f"Memory: {mem}MB", "Status": status, "Score": 1 if status == "PASS" else 0, "Feedback": f"{conf.get('MemorySize', 'N/A')}MB" if conf else "N/A"})
        
        # 4. Timeout Point
        status = "PASS" if conf and conf.get('Timeout') == timeout else "FAIL"
        points.append({"Category": f"9. Lambda: {name}", "Item": f"Timeout: {timeout}s", "Status": status, "Score": 1 if status == "PASS" else 0, "Feedback": f"{conf.get('Timeout', 'N/A')}s" if conf else "N/A"})
        
        # 5. Handler Point
        status = "PASS" if conf and conf.get('Handler') == handler else "FAIL"
        points.append({"Category": f"9. Lambda: {name}", "Item": f"Handler: {handler}", "Status": status, "Score": 1 if status == "PASS" else 0, "Feedback": conf.get('Handler', 'N/A') if conf else "N/A"})

            # 6. VPC Integration Point
        vpc_ok = conf and 'VpcConfig' in conf and conf['VpcConfig'].get('VpcId')
        points.append({"Category": f"9. Lambda: {name}", "Item": "VPC Integration", "Status": "PASS" if vpc_ok else "FAIL", "Score": 1 if vpc_ok else 0, "Feedback": "Connected" if vpc_ok else "Isolated/Disconnected"})
        
        # 7. Layer Integration Point (NEW)
        has_layers = conf and len(conf.get('Layers', [])) > 0
        points.append({"Category": f"9. Lambda: {name}", "Item": "Layer Integration (Psycopg2)", "Status": "PASS" if has_layers else "FAIL", "Score": 1 if has_layers else 0, "Feedback": "Attached" if has_layers else "Missing"})

    # --- API Gateway Section ---
    try:
        apis = apg.get_rest_apis()['items']
        br_api = next((a for a in apis if a['name'] == 'bank-recognition-api'), None)
        
        # Always check these attributes for the API
        status = "PASS" if br_api else "FAIL"
        points.append({"Category": "10. API Gateway", "Item": "API Existence", "Status": status, "Score": 1 if status == "PASS" else 0, "Feedback": "bank-recognition-api"})
        
        # Regional check
        reg_ok = br_api and 'REGIONAL' in br_api.get('endpointConfiguration', {}).get('types', [])
        points.append({"Category": "10. API Gateway", "Item": "Endpoint Type: REGIONAL", "Status": "PASS" if reg_ok else "FAIL", "Score": 1 if reg_ok else 0, "Feedback": "REGIONAL" if reg_ok else "N/A"})

        # Resource Paths
        resources = []
        if br_api:
            resources = apg.get_resources(restApiId=br_api['id'])['items']
        
        for path in ['/auth', '/ingest', '/query']:
            res = next((r for r in resources if r['path'] == path), None)
            points.append({"Category": f"10. API Resource: {path}", "Item": "1. Resource Existence", "Status": "PASS" if res else "FAIL", "Score": 1 if res else 0, "Feedback": "Found" if res else "Missing"})
            
            # Method Check
            has_post = res and 'POST' in res.get('resourceMethods', {})
            points.append({"Category": f"10. API Resource: {path}", "Item": "2. Method: POST", "Status": "PASS" if has_post else "FAIL", "Score": 1 if has_post else 0, "Feedback": "Configured" if has_post else "N/A"})
            
            # OPTIONS Method Check (NEW)
            has_options = res and 'OPTIONS' in res.get('resourceMethods', {})
            points.append({"Category": f"10. API Resource: {path}", "Item": "3. Method: OPTIONS (CORS)", "Status": "PASS" if has_options else "FAIL", "Score": 1 if has_options else 0, "Feedback": "CORS Enabled" if has_options else "Missing"})
            
            # Integration Check (NEW)
            is_proxy = False
            if res and has_post:
                try:
                    integ = apg.get_integration(restApiId=br_api['id'], resourceId=res['id'], httpMethod='POST')
                    is_proxy = integ['type'] == 'AWS_PROXY'
                except: pass
            points.append({"Category": f"10. API Resource: {path}", "Item": "4. Integration: Lambda Proxy", "Status": "PASS" if is_proxy else "FAIL", "Score": 1 if is_proxy else 0, "Feedback": "Enabled" if is_proxy else "Missing"})
            
    except:
        pass

    return points
