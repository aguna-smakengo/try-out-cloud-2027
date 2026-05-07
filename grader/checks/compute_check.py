import boto3

def check_compute_compliance(lmb, apg):
    points = []
    
    # --- 1. LAMBDA MICRO-AUDIT (EVERY DETAIL IS A POINT) ---
    required_lambdas = [
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
        except: pass

        cat = f"9. Lambda: {name}"
        points.append({"Category": cat, "Item": "1. Existence", "Status": "PASS" if conf else "FAIL", "Score": 1 if conf else 0, "Feedback": "Found" if conf else "Missing"})
        points.append({"Category": cat, "Item": f"2. Runtime: {runtime}", "Status": "PASS" if conf and conf.get('Runtime') == runtime else "FAIL", "Score": 1 if conf and conf.get('Runtime') == runtime else 0, "Feedback": conf.get('Runtime', 'N/A') if conf else "N/A"})
        points.append({"Category": cat, "Item": f"3. Memory: {mem}MB", "Status": "PASS" if conf and conf.get('MemorySize') == mem else "FAIL", "Score": 1 if conf and conf.get('MemorySize') == mem else 0, "Feedback": f"{conf.get('MemorySize', 'N/A')}MB" if conf else "N/A"})
        points.append({"Category": cat, "Item": f"4. Timeout: {timeout}s", "Status": "PASS" if conf and conf.get('Timeout') == timeout else "FAIL", "Score": 1 if conf and conf.get('Timeout') == timeout else 0, "Feedback": f"{conf.get('Timeout', 'N/A')}s" if conf else "N/A"})
        points.append({"Category": cat, "Item": f"5. Handler: {handler}", "Status": "PASS" if conf and conf.get('Handler') == handler else "FAIL", "Score": 1 if conf and conf.get('Handler') == handler else 0, "Feedback": conf.get('Handler', 'N/A') if conf else "N/A"})
        vpc_ok = conf and 'VpcConfig' in conf and conf['VpcConfig'].get('VpcId')
        points.append({"Category": cat, "Item": "6. VPC Integration", "Status": "PASS" if vpc_ok else "FAIL", "Score": 1 if vpc_ok else 0, "Feedback": "Connected" if vpc_ok else "Disconnected"})
        # Layer Check
        has_layers = conf and len(conf.get('Layers', [])) > 0
        points.append({"Category": cat, "Item": "7. Layer Integration (Psycopg2)", "Status": "PASS" if has_layers else "FAIL", "Score": 1 if has_layers else 0, "Feedback": "Attached" if has_layers else "Missing"})

    # --- 2. API GATEWAY MICRO-GRANULARITY ---
    try:
        apis = apg.get_rest_apis()['items']
        br_api = next((a for a in apis if a['name'] == 'bank-recognition-api'), None)
        
        cat_api = "10. API Gateway"
        points.append({"Category": cat_api, "Item": "1. API Existence", "Status": "PASS" if br_api else "FAIL", "Score": 1 if br_api else 0, "Feedback": "bank-recognition-api"})
        reg_ok = br_api and 'REGIONAL' in br_api.get('endpointConfiguration', {}).get('types', [])
        points.append({"Category": cat_api, "Item": "2. Endpoint Type: REGIONAL", "Status": "PASS" if reg_ok else "FAIL", "Score": 1 if reg_ok else 0, "Feedback": "REGIONAL" if reg_ok else "N/A"})

        resources = []
        if br_api: resources = apg.get_resources(restApiId=br_api['id'])['items']
        
        for path in ['/auth', '/ingest', '/query']:
            res = next((r for r in resources if r['path'] == path), None)
            points.append({"Category": f"11. API Path: {path}", "Item": "1. Resource Existence", "Status": "PASS" if res else "FAIL", "Score": 1 if res else 0, "Feedback": "Found" if res else "Missing"})
            
            methods = res.get('resourceMethods', {}) if res else {}
            # POST
            points.append({"Category": f"11. API Path: {path}", "Item": "2. Method: POST", "Status": "PASS" if 'POST' in methods else "FAIL", "Score": 1 if 'POST' in methods else 0, "Feedback": "Configured"})
            # OPTIONS
            points.append({"Category": f"11. API Path: {path}", "Item": "3. Method: OPTIONS (CORS)", "Status": "PASS" if 'OPTIONS' in methods else "FAIL", "Score": 1 if 'OPTIONS' in methods else 0, "Feedback": "Configured"})
            # Integration
            is_proxy = False
            if res and 'POST' in methods:
                try:
                    integ = apg.get_integration(restApiId=br_api['id'], resourceId=res['id'], httpMethod='POST')
                    is_proxy = integ['type'] == 'AWS_PROXY'
                except: pass
            points.append({"Category": f"11. API Path: {path}", "Item": "4. Integration: Lambda Proxy", "Status": "PASS" if is_proxy else "FAIL", "Score": 1 if is_proxy else 0, "Feedback": "Enabled" if is_proxy else "Missing"})
            
    except: pass

    return points
