import boto3
import os
import sys
import json
from datetime import datetime

# Add checks directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from checks.vpc_check import check_vpc_compliance
from checks.cloudformation_check import check_cf_compliance
from checks.database_check import check_database_compliance
from checks.compute_check import check_compute_compliance
from checks.storage_check import check_storage_compliance
from checks.automation_check import check_automation_compliance

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
            "api_url": "Not Found",
            "alb_url": "Amplify Console (Manual)"
        }

    def log(self, message):
        if self.progress_callback:
            self.progress_callback(message)
        print(f"[*] {message}")

    def run_all_checks(self):
        self.log("🚀 Initializing Recognition Vault Audit Engine...")
        
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

        # 1. CloudFormation
        self.log("🔍 Auditing CloudFormation Stacks...")
        self.results.extend(check_cf_compliance(cf))

        # 2. Networking
        self.log("🔍 Inspecting VPC & Network Isolation...")
        self.results.extend(check_vpc_compliance(ec2))

        # 3. Storage
        self.log("🔍 Checking Biometric S3 Vault...")
        self.results.extend(check_storage_compliance(s3, sts))

        # 4. Database
        self.log("🔍 Validating RDS (Postgres 15) & DynamoDB...")
        self.results.extend(check_database_compliance(rds, ddb))

        # 5. Automation
        self.log("🔍 Verifying SQS Pipeline & EventBridge...")
        self.results.extend(check_automation_compliance(sqs, eb))

        # 6. Compute
        self.log("🔍 Scanning Lambda Microservices & API Gateway...")
        self.results.extend(check_compute_compliance(lmb, apg))

        # Discovery Metadata (For Dashboard)
        self.log("🌐 Discovering Entry Points...")
        try:
            apis = apg.get_rest_apis()['items']
            br_api = next((a for a in apis if a['name'] == 'bank-recognition-api'), None)
            if br_api:
                self.discovery_metadata["api_url"] = f"https://{br_api['id']}.execute-api.us-east-1.amazonaws.com/prod"
            
            apps = amp.list_apps()['apps']
            br_app = next((a for a in apps if 'bank-recognition' in a['name'].lower()), None)
            if br_app:
                self.discovery_metadata["alb_url"] = f"https://master.{br_app['defaultDomain']}"
        except: pass

        self.log("✅ Audit Complete. Finalizing Report...")
        return self.results

if __name__ == "__main__":
    # For local CLI testing
    import sys
    if len(sys.argv) < 3:
        print("Usage: python validate_infrastructure.py <access_key> <secret_key> [session_token]")
        sys.exit(1)
    
    grader = InfrastructureGrader(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv)>3 else None)
    results = grader.run_all_checks()
    print(f"\nAudit completed with {len(results)} points evaluated.")
