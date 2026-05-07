import boto3

def check_storage_compliance(s3, sts):
    points = []
    try:
        account_id = sts.get_caller_identity()['Account']
        bucket_name = f"bank-recognition-uploads-{account_id}"
        try:
            s3.head_bucket(Bucket=bucket_name)
            points.append({"Category": "7. Storage", "Item": "S3 Vault Existence", "Status": "PASS", "Score": 1, "Feedback": bucket_name})
            pab = s3.get_public_access_block(Bucket=bucket_name)['PublicAccessBlockConfiguration']
            for key in ['BlockPublicAcls', 'IgnorePublicAcls', 'BlockPublicPolicy', 'RestrictPublicBuckets']:
                val = pab.get(key, False)
                points.append({"Category": "7. Storage", "Item": f"S3 Security: {key}", "Status": "PASS" if val else "FAIL", "Score": 1 if val else 0, "Feedback": "Enabled" if val else "Disabled"})
        except:
            points.append({"Category": "7. Storage", "Item": "S3 Vault Existence", "Status": "FAIL", "Score": 0, "Feedback": "Not found"})
    except:
        points.append({"Category": "7. Storage", "Item": "Storage Audit", "Status": "FAIL", "Score": 0, "Feedback": "Error"})
    return points
