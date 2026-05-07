import boto3

def check_amplify_compliance(amp):
    points = []
    
    try:
        apps = amp.list_apps()['apps']
        br_app = next((a for a in apps if 'bank-recognition' in a['name'].lower()), None)
        
        if br_app:
            app_id = br_app['appId']
            # Existence (1 pt)
            points.append({"Category": "7. Amplify Frontend", "Item": "Amplify App Existence", "Status": "PASS", "Score": 1, "Feedback": "Found"})
            # Naming (1 pt)
            status = "PASS" if 'bank-recognition' in br_app['name'].lower() else "FAIL"
            points.append({"Category": "7. Amplify Frontend", "Item": "Amplify App Naming", "Status": status, "Score": 1 if status == "PASS" else 0, "Feedback": br_app['name']})
            # Repository Connection (1 pt)
            has_repo = 'repository' in br_app and br_app['repository']
            points.append({"Category": "7. Amplify Frontend", "Item": "GitHub Repository Link", "Status": "PASS" if has_repo else "FAIL", "Score": 1 if has_repo else 0, "Feedback": br_app.get('repository', 'Not Linked')})
            
            # Check Branches
            branches = amp.list_branches(appId=app_id)['branches']
            if branches:
                points.append({"Category": "7. Amplify Frontend", "Item": "Production Branch Created", "Status": "PASS", "Score": 1, "Feedback": f"Found branch: {branches[0]['branchName']}"})
                # Check Build Status (Optional 1 pt)
                status = branches[0]['stage']
                points.append({"Category": "7. Amplify Frontend", "Item": "Branch Stage: PRODUCTION", "Status": "PASS" if status == 'PRODUCTION' else "FAIL", "Score": 1 if status == 'PRODUCTION' else 0, "Feedback": status})
            else:
                points.append({"Category": "7. Amplify Frontend", "Item": "Production Branch", "Status": "FAIL", "Score": 0, "Feedback": "No branches found"})
        else:
            points.append({"Category": "7. Amplify Frontend", "Item": "Amplify App Existence", "Status": "FAIL", "Score": 0, "Feedback": "No Amplify app matching 'bank-recognition' found"})

    except Exception as e:
        points.append({"Category": "7. Amplify Frontend", "Item": "Amplify Audit Error", "Status": "FAIL", "Score": 0, "Feedback": str(e)})

    return points
