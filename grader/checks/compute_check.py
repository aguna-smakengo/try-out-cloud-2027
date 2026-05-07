import boto3

def check_compute_compliance(lmb, apg):
    points = []
    
    # Configuration Standards
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
        # Existence
        status = "PASS" if conf else "FAIL"
        points.append({
            "Category": cat, "Item": "Existence", 
            "Status": status, "Score": 1 if status == "PASS" else 0, 
            "Expected": "Exist", "Actual": "Found" if conf else "Missing",
            "Feedback": "Microservice presence"
        })
        
        # Runtime
        act_runtime = conf.get('Runtime', 'N/A') if conf else "N/A"
        status = "PASS" if act_runtime == runtime else "FAIL"
        points.append({
            "Category": cat, "Item": f"Runtime: {runtime}", 
            "Status": status, "Score": 1 if status == "PASS" else 0, 
            "Expected": runtime, "Actual": act_runtime,
            "Feedback": "Standardized environment"
        })
        
        # Memory
        act_mem = conf.get('MemorySize', 'N/A') if conf else "N/A"
        status = "PASS" if str(act_mem) == str(mem) else "FAIL"
        points.append({
            "Category": cat, "Item": f"Memory: {mem}MB", 
            "Status": status, "Score": 1 if status == "PASS" else 0, 
            "Expected": f"{mem}MB", "Actual": f"{act_mem}MB",
            "Feedback": "Resource allocation"
        })
        
        # Timeout
        act_timeout = conf.get('Timeout', 'N/A') if conf else "N/A"
        status = "PASS" if str(act_timeout) == str(timeout) else "FAIL"
        points.append({
            "Category": cat, "Item": f"Timeout: {timeout}s", 
            "Status": status, "Score": 1 if status == "PASS" else 0, 
            "Expected": f"{timeout}s", "Actual": f"{act_timeout}s",
            "Feedback": "Execution threshold"
        })
        
        # Handler
        act_handler = conf.get('Handler', 'N/A') if conf else "N/A"
        status = "PASS" if act_handler == handler else "FAIL"
        points.append({
            "Category": cat, "Item": f"Handler: {handler}", 
            "Status": status, "Score": 1 if status == "PASS" else 0, 
            "Expected": handler, "Actual": act_handler,
            "Feedback": "Entry point validation"
        })

        # VPC
        vpc_ok = conf and 'VpcConfig' in conf and conf['VpcConfig'].get('VpcId')
        points.append({
            "Category": cat, "Item": "VPC Integration", 
            "Status": "PASS" if vpc_ok else "FAIL", "Score": 1 if vpc_ok else 0, 
            "Expected": "VPC-Attached", "Actual": "Connected" if vpc_ok else "Isolated",
            "Feedback": "Internal network access"
        })
        
        # Layer
        has_layers = conf and len(conf.get('Layers', [])) > 0
        points.append({
            "Category": cat, "Item": "Layer Integration (Psycopg2)", 
            "Status": "PASS" if has_layers else "FAIL", "Score": 1 if has_layers else 0, 
            "Expected": "Attached", "Actual": "Found" if has_layers else "Missing",
            "Feedback": "Dependency management"
        })

    # --- API Gateway ---
    try:
        apis = apg.get_rest_apis()['items']
        br_api = next((a for a in apis if a['name'] == 'bank-recognition-api'), None)
        cat_api = "10. API Gateway"
        
        points.append({
            "Category": cat_api, "Item": "API Existence", 
            "Status": "PASS" if br_api else "FAIL", "Score": 1 if br_api else 0, 
            "Expected": "bank-recognition-api", "Actual": "Found" if br_api else "Missing",
            "Feedback": "Main ingress point"
        })
        
        reg_ok = br_api and 'REGIONAL' in br_api.get('endpointConfiguration', {}).get('types', [])
        points.append({
            "Category": cat_api, "Item": "Endpoint Type: REGIONAL", 
            "Status": "PASS" if reg_ok else "FAIL", "Score": 1 if reg_ok else 0, 
            "Expected": "REGIONAL", "Actual": "REGIONAL" if reg_ok else "N/A",
            "Feedback": "Deployment strategy"
        })

        resources = []
        if br_api: resources = apg.get_resources(restApiId=br_api['id'])['items']
        
        for path in ['/auth', '/ingest', '/query']:
            res = next((r for r in resources if r['path'] == path), None)
            cat_p = f"10. API Resource: {path}"
            points.append({
                "Category": cat_p, "Item": "Resource Existence", 
                "Status": "PASS" if res else "FAIL", "Score": 1 if res else 0, 
                "Expected": "Exist", "Actual": "Found" if res else "Missing",
                "Feedback": "Path presence"
            })
            
            methods = res.get('resourceMethods', {}) if res else {}
            has_post = 'POST' in methods
            points.append({
                "Category": cat_p, "Item": "Method: POST", 
                "Status": "PASS" if has_post else "FAIL", "Score": 1 if has_post else 0, 
                "Expected": "POST", "Actual": "Configured" if has_post else "N/A",
                "Feedback": "Write operations support"
            })
            
            has_options = 'OPTIONS' in methods
            points.append({
                "Category": cat_p, "Item": "Method: OPTIONS (CORS)", 
                "Status": "PASS" if has_options else "FAIL", "Score": 1 if has_options else 0, 
                "Expected": "OPTIONS", "Actual": "Configured" if has_options else "Missing",
                "Feedback": "Cross-Origin support"
            })
            
            is_proxy = False
            if res and has_post:
                try:
                    integ = apg.get_integration(restApiId=br_api['id'], resourceId=res['id'], httpMethod='POST')
                    is_proxy = integ['type'] == 'AWS_PROXY'
                except: pass
            points.append({
                "Category": cat_p, "Item": "Integration: Lambda Proxy", 
                "Status": "PASS" if is_proxy else "FAIL", "Score": 1 if is_proxy else 0, 
                "Expected": "AWS_PROXY", "Actual": "Enabled" if is_proxy else "N/A",
                "Feedback": "Serverless integration type"
            })
            
    except: pass

    return points
