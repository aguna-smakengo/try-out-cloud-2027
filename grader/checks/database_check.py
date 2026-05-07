import boto3

def check_database_compliance(rds, ddb):
    points = []
    try:
        instances = rds.describe_db_instances(DBInstanceIdentifier='bank-recognition-db')['DBInstances']
        exists = "PASS" if instances else "FAIL"
        points.append({
            "Category": "6. Database", "Item": "RDS Instance Existence", 
            "Status": exists, "Score": 1 if exists == "PASS" else 0, 
            "Expected": "bank-recognition-db", "Actual": "Found" if instances else "Missing",
            "Feedback": "Relational store presence"
        })
        if instances:
            db = instances[0]
            points.append({
                "Category": "6. Database", "Item": "RDS Engine: PostgreSQL", 
                "Status": "PASS" if db['Engine'] == 'postgres' else "FAIL", "Score": 1 if db['Engine'] == 'postgres' else 0, 
                "Expected": "postgres", "Actual": db['Engine'],
                "Feedback": "Database engine validation"
            })
            points.append({
                "Category": "6. Database", "Item": "RDS Version: 15.x", 
                "Status": "PASS" if db['EngineVersion'].startswith('15') else "FAIL", "Score": 1 if db['EngineVersion'].startswith('15') else 0, 
                "Expected": "15.x", "Actual": db['EngineVersion'],
                "Feedback": "Major version compliance"
            })
            points.append({
                "Category": "6. Database", "Item": "RDS Storage: gp2", 
                "Status": "PASS" if db['StorageType'] == 'gp2' else "FAIL", "Score": 1 if db['StorageType'] == 'gp2' else 0, 
                "Expected": "gp2", "Actual": db['StorageType'],
                "Feedback": "EBS Volume type"
            })
            points.append({
                "Category": "6. Database", "Item": "RDS Public Access: Disabled", 
                "Status": "PASS" if not db['PubliclyAccessible'] else "FAIL", "Score": 1 if not db['PubliclyAccessible'] else 0, 
                "Expected": "False", "Actual": str(db['PubliclyAccessible']),
                "Feedback": "Network security isolation"
            })

        table = ddb.describe_table(TableName='bank-recognition-results')['Table']
        points.append({
            "Category": "6. Database", "Item": "DynamoDB Table Existence", 
            "Status": "PASS", "Score": 1, 
            "Expected": "bank-recognition-results", "Actual": "Found",
            "Feedback": "NoSQL store presence"
        })
        pk = next((k['AttributeName'] for k in table['KeySchema'] if k['KeyType'] == 'HASH'), "N/A")
        points.append({
            "Category": "6. Database", "Item": "DynamoDB PK: imageId", 
            "Status": "PASS" if pk == 'imageId' else "FAIL", "Score": 1 if pk == 'imageId' else 0, 
            "Expected": "imageId", "Actual": pk,
            "Feedback": "Schema partition key"
        })
        bm = table.get('BillingModeSummary', {}).get('BillingMode', 'PROVISIONED')
        points.append({
            "Category": "6. Database", "Item": "DynamoDB Billing: PAY_PER_REQUEST", 
            "Status": "PASS" if bm == 'PAY_PER_REQUEST' else "FAIL", "Score": 1 if bm == 'PAY_PER_REQUEST' else 0, 
            "Expected": "PAY_PER_REQUEST", "Actual": bm,
            "Feedback": "Cost optimization mode"
        })
    except:
        points.append({"Category": "6. Database", "Item": "Database Audit", "Status": "FAIL", "Score": 0, "Expected": "Resource Found", "Actual": "Error/Missing", "Feedback": "Check failed"})
    return points
