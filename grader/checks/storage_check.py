import boto3

def check_storage_compliance(s3, sts):
    points = []
    
    try:
        account_id = sts.get_caller_identity()['Account']
        bucket_name = f"bank-recognition-uploads-{account_id}"
        
        try:
            s3.head_bucket(Bucket=bucket_name)
            points.append({
                "Category": "5. Storage", "Item": "S3 Biometric Vault",
                "Status": "PASS", "Score": 30,
                "Expected": bucket_name, "Actual": "Found",
                "Feedback": "Account-specific S3 bucket for uploads"
            })
            
            pab = s3.get_public_access_block(Bucket=bucket_name)['PublicAccessBlockConfiguration']
            status = "PASS" if pab['BlockPublicAcls'] and pab['IgnorePublicAcls'] else "FAIL"
            points.append({
                "Category": "5. Storage", "Item": "S3 Public Access Block",
                "Status": status, "Score": 20 if status == "PASS" else 0,
                "Expected": "ENABLED", "Actual": "ENABLED" if status == "PASS" else "DISABLED",
                "Feedback": "Data must be protected from public access"
            })
        except:
            points.append({"Category": "5. Storage", "Item": "S3 Biometric Vault", "Status": "FAIL", "Score": 0, "Feedback": f"Bucket {bucket_name} not found"})

    except:
        points.append({"Category": "5. Storage", "Item": "S3 Audit Error", "Status": "FAIL", "Score": 0, "Feedback": "Error during discovery"})

    return points
