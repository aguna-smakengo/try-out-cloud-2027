import boto3

def check_database_compliance(rds, ddb):
    points = []
    
    # 1. RDS Micro-Audit
    try:
        instances = rds.describe_db_instances(DBInstanceIdentifier='bank-recognition-db')['DBInstances']
        exists = "PASS" if instances else "FAIL"
        points.append({"Category": "3. RDS", "Item": "RDS Existence", "Status": exists, "Score": 1 if exists == "PASS" else 0, "Feedback": "bank-recognition-db"})
        
        if instances:
            db = instances[0]
            # Engine (1 pt)
            status = "PASS" if db['Engine'] == 'postgres' else "FAIL"
            points.append({"Category": "3. RDS", "Item": "RDS Engine: PostgreSQL", "Status": status, "Score": 1 if status == "PASS" else 0, "Feedback": db['Engine']})
            # Version (1 pt)
            status = "PASS" if db['EngineVersion'].startswith('15') else "FAIL"
            points.append({"Category": "3. RDS", "Item": "RDS Version: 15.x", "Status": status, "Score": 1 if status == "PASS" else 0, "Feedback": db['EngineVersion']})
            # Instance Class (1 pt)
            points.append({"Category": "3. RDS", "Item": "RDS Instance Class: db.t3.micro", "Status": "PASS" if db['DBInstanceClass'] == 'db.t3.micro' else "FAIL", "Score": 1, "Feedback": db['DBInstanceClass']})
            # Public Access (1 pt)
            points.append({"Category": "3. RDS", "Item": "RDS Private Isolation", "Status": "PASS" if not db['PubliclyAccessible'] else "FAIL", "Score": 1, "Feedback": "Secured" if not db['PubliclyAccessible'] else "Public!"})
    except:
        points.append({"Category": "3. RDS", "Item": "RDS Audit", "Status": "FAIL", "Score": 0, "Feedback": "Failed"})

    # 2. DynamoDB Micro-Audit
    try:
        table = ddb.describe_table(TableName='bank-recognition-results')['Table']
        points.append({"Category": "3. DynamoDB", "Item": "DynamoDB Existence", "Status": "PASS", "Score": 1, "Feedback": "bank-recognition-results"})
        # PK (1 pt)
        ks = table['KeySchema']
        pk = next((k['AttributeName'] for k in ks if k['KeyType'] == 'HASH'), None)
        points.append({"Category": "3. DynamoDB", "Item": "PK: imageId", "Status": "PASS" if pk == 'imageId' else "FAIL", "Score": 1, "Feedback": pk})
        # SK (1 pt)
        sk = next((k['AttributeName'] for k in ks if k['KeyType'] == 'RANGE'), None)
        points.append({"Category": "3. DynamoDB", "Item": "SK: timestamp", "Status": "PASS" if sk == 'timestamp' else "FAIL", "Score": 1, "Feedback": sk})
        # Billing Mode (1 pt)
        bm = table.get('BillingModeSummary', {}).get('BillingMode', 'PROVISIONED')
        points.append({"Category": "3. DynamoDB", "Item": "Billing: PAY_PER_REQUEST", "Status": "PASS" if bm == 'PAY_PER_REQUEST' else "FAIL", "Score": 1, "Feedback": bm})
    except:
        points.append({"Category": "3. DynamoDB", "Item": "DynamoDB Audit", "Status": "FAIL", "Score": 0, "Feedback": "Failed"})

    return points
