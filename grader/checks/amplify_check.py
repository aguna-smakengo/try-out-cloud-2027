import boto3

def check_amplify_compliance(amp):
    points = []
    try:
        apps = amp.list_apps()['apps']
        br_app = next((a for a in apps if 'bank-recognition' in a['name'].lower()), None)
        if br_app:
            points.append({"Category": "11. Amplify", "Item": "App Existence", "Status": "PASS", "Score": 1, "Feedback": "Found"})
            points.append({"Category": "11. Amplify", "Item": "Repository Linked", "Status": "PASS" if 'repository' in br_app and br_app['repository'] else "FAIL", "Score": 1 if 'repository' in br_app else 0, "Feedback": "Connected"})
            branches = amp.list_branches(appId=br_app['appId'])['branches']
            if branches:
                points.append({"Category": "11. Amplify", "Item": "Production Branch Created", "Status": "PASS", "Score": 1, "Feedback": branches[0]['branchName']})
                points.append({"Category": "11. Amplify", "Item": "Branch Stage: PRODUCTION", "Status": "PASS" if branches[0]['stage'] == 'PRODUCTION' else "FAIL", "Score": 1 if branches[0]['stage'] == 'PRODUCTION' else 0, "Feedback": branches[0]['stage']})
        else:
            points.append({"Category": "11. Amplify", "Item": "App Existence", "Status": "FAIL", "Score": 0, "Feedback": "Missing"})
    except:
        points.append({"Category": "11. Amplify", "Item": "Amplify Audit", "Status": "FAIL", "Score": 0, "Feedback": "Error"})
    return points
