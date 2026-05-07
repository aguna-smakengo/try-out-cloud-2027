import boto3

def check_database_compliance(rds, ddb):
    points = []
    
    # 1. RDS Audit
    try:
        instances = rds.describe_db_instances(DBInstanceIdentifier='bank-recognition-db')['DBInstances']
        status = "PASS" if instances else "FAIL"
        points.append({
            "Category": "3. Persistence", "Item": "RDS Instance Existence",
            "Status": status, "Score": 15 if status == "PASS" else 0,
            "Expected": "bank-recognition-db", "Actual": "Found" if instances else "Missing",
            "Feedback": "Relational store must exist"
        })
        
        if instances:
            db = instances[0]
            # Engine Version 15
            is_v15 = db['EngineVersion'].startswith('15')
            points.append({
                "Category": "3. Persistence", "Item": "RDS Engine: PostgreSQL 15",
                "Status": "PASS" if is_v15 else "FAIL", "Score": 15 if is_v15 else 0,
                "Expected": "PostgreSQL 15.x", "Actual": f"{db['Engine']} {db['EngineVersion']}",
                "Feedback": "Mandatory database engine version"
            })
            
            # Private Isolation
            is_private = not db['PubliclyAccessible']
            points.append({
                "Category": "3. Persistence", "Item": "RDS Network Isolation",
                "Status": "PASS" if is_private else "FAIL", "Score": 10 if is_private else 0,
                "Expected": "PubliclyAccessible=False", "Actual": str(not is_private),
                "Feedback": "RDS must not be reachable from public internet"
            })
    except:
        points.append({"Category": "3. Persistence", "Item": "RDS Audit Error", "Status": "FAIL", "Score": 0, "Feedback": "Instance not found or error"})

    # 2. DynamoDB Audit
    try:
        table = ddb.describe_table(TableName='bank-recognition-results')['Table']
        points.append({
            "Category": "3. Persistence", "Item": "DynamoDB Table Existence",
            "Status": "PASS", "Score": 15,
            "Expected": "bank-recognition-results", "Actual": "Found",
            "Feedback": "NoSQL results store must exist"
        })
        
        ks = table['KeySchema']
        pk = next((k['AttributeName'] for k in ks if k['KeyType'] == 'HASH'), None)
        sk = next((k['AttributeName'] for k in ks if k['KeyType'] == 'RANGE'), None)
        schema_ok = (pk == 'imageId' and sk == 'timestamp')
        
        points.append({
            "Category": "3. Persistence", "Item": "DynamoDB Schema (PK/SK)",
            "Status": "PASS" if schema_ok else "FAIL", "Score": 15 if schema_ok else 0,
            "Expected": "HASH(imageId), RANGE(timestamp)", "Actual": f"HASH({pk}), RANGE({sk})",
            "Feedback": "Required schema for AI result indexing"
        })
    except:
        points.append({"Category": "3. Persistence", "Item": "DynamoDB Audit Error", "Status": "FAIL", "Score": 0, "Feedback": "Table not found"})

    return points
