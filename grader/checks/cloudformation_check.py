import boto3

def check_cf_compliance(cf):
    points = []
    
    try:
        stacks = cf.describe_stacks()['Stacks']
        active_stacks = [s['StackName'] for s in stacks if s['StackStatus'] in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']]
        
        required_stacks = [
            'bank-recognition-networking',
            'bank-recognition-storage',
            'bank-recognition-database',
            'bank-recognition-automation',
            'bank-recognition-compute',
            'bank-recognition-api'
        ]
        
        for stack_name in required_stacks:
            status = "PASS" if stack_name in active_stacks else "FAIL"
            points.append({
                "Category": "2. Infrastructure as Code", "Item": f"Stack Tier: {stack_name}",
                "Status": status, "Score": 10 if status == "PASS" else 0,
                "Expected": "CREATE_COMPLETE", "Actual": status,
                "Feedback": f"Every tier must be deployed as a separate CloudFormation stack"
            })

        # Global CF check
        any_cf = any(s.startswith('bank-recognition-') for s in active_stacks)
        points.append({
            "Category": "2. Infrastructure as Code", "Item": "CloudFormation Usage (Mandatory)",
            "Status": "PASS" if any_cf else "FAIL", "Score": 40 if any_cf else 0,
            "Expected": "TRUE", "Actual": str(any_cf).upper(),
            "Feedback": "Nilai 0 jika tidak menggunakan CloudFormation!"
        })

    except Exception as e:
        points.append({"Category": "2. Infrastructure as Code", "Item": "CF Audit Error", "Status": "FAIL", "Score": 0, "Feedback": str(e)})

    return points
