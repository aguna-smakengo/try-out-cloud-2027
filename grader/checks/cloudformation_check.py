import boto3

def check_cf_compliance(cf):
    points = []
    try:
        # Get all stacks (including those in rollback or failed states)
        # We filter out only DELETE_COMPLETE
        stacks = cf.describe_stacks()['Stacks']
        
        # Mapping of existing stacks
        existing_stacks = {s['StackName']: s['StackStatus'] for s in stacks if s['StackStatus'] != 'DELETE_COMPLETE'}
        
        required_stacks = [
            'bank-recognition-networking', 'bank-recognition-storage',
            'bank-recognition-database', 'bank-recognition-automation',
            'bank-recognition-compute', 'bank-recognition-api'
        ]
        
        for stack_name in required_stacks:
            current_status = existing_stacks.get(stack_name)
            # If stack exists in ANY state (Rollback, Failed, Update_Failed, etc), give 1 point
            status_pass = current_status is not None
            
            points.append({
                "Category": "5. CloudFormation", "Item": f"Stack Tier: {stack_name}",
                "Status": "PASS" if status_pass else "FAIL", 
                "Score": 1 if status_pass else 0,
                "Expected": "Exist (Any Status)", 
                "Actual": current_status if status_pass else "NOT_FOUND",
                "Feedback": f"Infrastructure was deployed (Current Status: {current_status})" if status_pass else "Stack not found in account"
            })

        # Mandatory Usage Check
        any_br_cf = any(name.startswith('bank-recognition-') for name in existing_stacks.keys())
        points.append({
            "Category": "5. CloudFormation", "Item": "IaC Mandatory Usage",
            "Status": "PASS" if any_br_cf else "FAIL", 
            "Score": 1 if any_br_cf else 0,
            "Expected": "TRUE", "Actual": "FOUND" if any_br_cf else "NONE",
            "Feedback": "Used CloudFormation for resource provisioning"
        })

    except Exception as e:
        points.append({"Category": "5. CloudFormation", "Item": "CF Audit Error", "Status": "FAIL", "Score": 0, "Feedback": str(e)})
        
    return points
