import boto3
import os
import sys
import json
from datetime import datetime

# Add checks directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import micro-audit checks
from checks.vpc_check import check_vpc_compliance
from checks.cloudformation_check import check_cf_compliance
from checks.database_check import check_database_compliance
from checks.compute_check import check_compute_compliance
from checks.storage_check import check_storage_compliance
from checks.automation_check import check_automation_compliance
from checks.amplify_check import check_amplify_compliance

class InfrastructureGrader:
    def __init__(self, access_key, secret_key, session_token=None, progress_callback=None):
        self.session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            aws_session_token=session_token,
            region_name='us-east-1'
        )
        self.progress_callback = progress_callback
        self.results = []
        self.discovery_metadata = {
            "api_url": "⚠️ API Gateway Not Found",
            "alb_url": "⚠️ Amplify Not Found (Check Console)"
        }

    def log(self, message):
        if self.progress_callback:
            self.progress_callback(message)
        print(f"[*] {message}")

    def run_all_checks(self):
        self.log("🚀 Initializing Recognition Vault INSANE-DETAIL Engine...")
        
        # Clients
        ec2 = self.session.client('ec2')
        cf = self.session.client('cloudformation')
        rds = self.session.client('rds')
        ddb = self.session.client('dynamodb')
        lmb = self.session.client('lambda')
        apg = self.session.client('apigateway')
        s3 = self.session.client('s3')
        sts = self.session.client('sts')
        sqs = self.session.client('sqs')
        eb = self.session.client('events')
        amp = self.session.client('amplify')

        # Run Modular Insane-Audits
        self.log("🔍 [1/7] Auditing CloudFormation Stacks...")
        self.results.extend(check_cf_compliance(cf))

        self.log("🔍 [2/7] Inspecting Networking Forensics...")
        self.results.extend(check_vpc_compliance(ec2))

        self.log("🔍 [3/7] Auditing Storage Security...")
        self.results.extend(check_storage_compliance(s3, sts))

        self.log("🔍 [4/7] Validating Database Internals...")
        self.results.extend(check_database_compliance(rds, ddb))

        self.log("🔍 [5/7] Verifying Automation Pipeline...")
        self.results.extend(check_automation_compliance(sqs, eb))

        self.log("🔍 [6/7] Scanning Compute & API Layers...")
        self.results.extend(check_compute_compliance(lmb, apg))

        self.log("🔍 [7/7] Auditing Amplify Deployment...")
        self.results.extend(check_amplify_compliance(amp))

        # Discovery Metadata (For Dashboard)
        try:
            apis = apg.get_rest_apis()['items']
            br_api = next((a for a in apis if a['name'] == 'bank-recognition-api'), None)
            if br_api:
                self.discovery_metadata["api_url"] = f"https://{br_api['id']}.execute-api.us-east-1.amazonaws.com/prod"
            
            apps = amp.list_apps()['apps']
            br_app = next((a for a in apps if 'bank-recognition' in a['name'].lower()), None)
            if br_app:
                branches = amp.list_branches(appId=br_app['appId'])['branches']
                master = next((b for b in branches if b['branchName'] in ['master', 'main']), None)
                if master:
                    self.discovery_metadata["alb_url"] = f"https://{master['branchName']}.{br_app['defaultDomain']}"
                else:
                    self.discovery_metadata["alb_url"] = "⚠️ App Found, but Branch Missing"
        except: pass

        # Sort results by Category then by Item for readability
        self.results = sorted(self.results, key=lambda x: (x['Category'], x['Item']))

        self.log("✅ Audit Complete. Results Sorted.")
        return self.results

if __name__ == "__main__":
    import sys
    grader = InfrastructureGrader(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv)>3 else None)
    results = grader.run_all_checks()
    print(f"Total Points: {len(results)}")
