import boto3

def check_amplify_compliance(amp):
    points = []
    try:
        apps = amp.list_apps()['apps']
        br_app = next((a for a in apps if 'bank-recognition' in a['name'].lower()), None)
        if br_app:
            points.append({
                "Category": "11. Amplify Frontend", "Item": "1. App Existence", 
                "Status": "PASS", "Score": 1, 
                "Expected": "bank-recognition*", "Actual": "Found",
                "Feedback": "Frontend hosting presence"
            })
            repo_ok = 'repository' in br_app and br_app['repository']
            points.append({
                "Category": "11. Amplify Frontend", "Item": "2. Repository Linked", 
                "Status": "PASS" if repo_ok else "FAIL", "Score": 1 if repo_ok else 0, 
                "Expected": "Connected", "Actual": "Verified" if repo_ok else "Missing",
                "Feedback": "CI/CD Git integration"
            })
            branches = amp.list_branches(appId=br_app['appId'])['branches']
            if branches:
                points.append({
                    "Category": "11. Amplify Frontend", "Item": "3. Production Branch Created", 
                    "Status": "PASS", "Score": 1, 
                    "Expected": "Exist", "Actual": branches[0]['branchName'],
                    "Feedback": "Deployment environment"
                })
                is_prod = branches[0]['stage'] == 'PRODUCTION'
                points.append({
                    "Category": "11. Amplify Frontend", "Item": "4. Branch Stage: PRODUCTION", 
                    "Status": "PASS" if is_prod else "FAIL", "Score": 1 if is_prod else 0, 
                    "Expected": "PRODUCTION", "Actual": branches[0]['stage'],
                    "Feedback": "Environment classification"
                })
        else:
            points.append({"Category": "11. Amplify Frontend", "Item": "1. App Existence", "Status": "FAIL", "Score": 0, "Expected": "Exist", "Actual": "Missing", "Feedback": "App not found"})
    except:
        points.append({"Category": "11. Amplify Frontend", "Item": "Audit", "Status": "FAIL", "Score": 0, "Expected": "Success", "Actual": "Error", "Feedback": "Discovery failed"})
    return points
