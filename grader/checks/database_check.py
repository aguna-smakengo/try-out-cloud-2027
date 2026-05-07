import boto3

def check_database_compliance(rds, ddb):
    points = []
    
    # --- 1. RDS INSANE AUDIT ---
    try:
        instances = rds.describe_db_instances(DBInstanceIdentifier='bank-recognition-db')['DBInstances']
        exists = "PASS" if instances else "FAIL"
        points.append({"Category": "5. RDS Persistence", "Item": "RDS: Create/Existence", "Status": exists, "Score": 1 if exists == "PASS" else 0, "Feedback": "bank-recognition-db"})
        
        if instances:
            db = instances[0]
            points.append({"Category": "5. RDS Persistence", "Item": "RDS: Name Compliance", "Status": "PASS", "Score": 1, "Feedback": "bank-recognition-db"})
            points.append({"Category": "5. RDS Persistence", "Item": "RDS: Engine (PostgreSQL)", "Status": "PASS" if db['Engine'] == 'postgres' else "FAIL", "Score": 1, "Feedback": db['Engine']})
            points.append({"Category": "5. RDS Persistence", "Item": "RDS: Version (15.x)", "Status": "PASS" if db['EngineVersion'].startswith('15') else "FAIL", "Score": 1, "Feedback": db['EngineVersion']})
            points.append({"Category": "5. RDS Persistence", "Item": "RDS: Class (db.t3.micro)", "Status": "PASS" if db['DBInstanceClass'] == 'db.t3.micro' else "FAIL", "Score": 1, "Feedback": db['DBInstanceClass']})
            points.append({"Category": "5. RDS Persistence", "Item": "RDS: Storage Type (gp2)", "Status": "PASS" if db['StorageType'] == 'gp2' else "FAIL", "Score": 1, "Feedback": db['StorageType']})
            points.append({"Category": "5. RDS Persistence", "Item": "RDS: Storage Size (20GB)", "Status": "PASS" if db['AllocatedStorage'] == 20 else "FAIL", "Score": 1, "Feedback": f"{db['AllocatedStorage']}GB"})
            points.append({"Category": "5. RDS Persistence", "Item": "RDS: Multi-AZ (Disabled)", "Status": "PASS" if not db['MultiAZ'] else "FAIL", "Score": 1, "Feedback": str(db['MultiAZ'])})
            points.append({"Category": "5. RDS Persistence", "Item": "RDS: Private Isolation", "Status": "PASS" if not db['PubliclyAccessible'] else "FAIL", "Score": 1, "Feedback": "Secured"})
            # Subnet Group (1 pt)
            sng = db.get('DBSubnetGroup', {}).get('DBSubnetGroupName', '')
            points.append({"Category": "5. RDS Persistence", "Item": "RDS: Subnet Group Config", "Status": "PASS" if sng else "FAIL", "Score": 1, "Feedback": sng})
    except:
        points.append({"Category": "5. RDS Persistence", "Item": "RDS Audit", "Status": "FAIL", "Score": 0, "Feedback": "Failed"})

    # --- 2. DYNAMODB INSANE AUDIT ---
    try:
        table = ddb.describe_table(TableName='bank-recognition-results')['Table']
        points.append({"Category": "6. DynamoDB", "Item": "Table: Create/Existence", "Status": "PASS", "Score": 1, "Feedback": "bank-recognition-results"})
        points.append({"Category": "6. DynamoDB", "Item": "Schema: PK (imageId)", "Status": "PASS" if table['KeySchema'][0]['AttributeName'] == 'imageId' else "FAIL", "Score": 1, "Feedback": "Correct"})
        points.append({"Category": "6. DynamoDB", "Item": "Schema: SK (timestamp)", "Status": "PASS" if len(table['KeySchema']) > 1 and table['KeySchema'][1]['AttributeName'] == 'timestamp' else "FAIL", "Score": 1, "Feedback": "Correct"})
        # Billing Mode (1 pt)
        bm = table.get('BillingModeSummary', {}).get('BillingMode', 'PROVISIONED')
        points.append({"Category": "6. DynamoDB", "Item": "Billing: PAY_PER_REQUEST", "Status": "PASS" if bm == 'PAY_PER_REQUEST' else "FAIL", "Score": 1, "Feedback": bm})
    except:
        points.append({"Category": "6. DynamoDB", "Item": "DynamoDB Audit", "Status": "FAIL", "Score": 0, "Feedback": "Failed"})

    return points
