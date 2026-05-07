import boto3

def check_storage_compliance(s3, sts):
    points = []
    
    try:
        account_id = sts.get_caller_identity()['Account']
        bucket_name = f"bank-recognition-uploads-{account_id}"
        
        try:
            s3.head_bucket(Bucket=bucket_name)
            points.append({"Category": "5. Storage", "Item": "S3 Bucket Existence", "Status": "PASS", "Score": 1, "Feedback": bucket_name})
            
            # Public Access Block (Micro-Audit per flag)
            pab = s3.get_public_access_block(Bucket=bucket_name)['PublicAccessBlockConfiguration']
            
            flags = [
                ('BlockPublicAcls', 'Block Public ACLs'),
                ('IgnorePublicAcls', 'Ignore Public ACLs'),
                ('BlockPublicPolicy', 'Block Public Policy'),
                ('RestrictPublicBuckets', 'Restrict Public Buckets')
            ]
            
            for key, label in flags:
                val = pab.get(key, False)
                points.append({
                    "Category": "5. Storage", "Item": f"S3 Security: {label}",
                    "Status": "PASS" if val else "FAIL", "Score": 1 if val else 0,
                    "Feedback": "Enabled" if val else "Disabled"
                })
        except:
            points.append({"Category": "5. Storage", "Item": "S3 Bucket Existence", "Status": "FAIL", "Score": 0, "Feedback": "Not found"})
    except:
        points.append({"Category": "5. Storage", "Item": "S3 Audit", "Status": "FAIL", "Score": 0, "Feedback": "Failed"})

    return points
