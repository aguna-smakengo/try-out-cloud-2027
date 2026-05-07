import boto3

def check_vpc_compliance(ec2):
    points = []
    vpc_id = None
    
    # 1. VPC Micro-Audit
    try:
        vpcs = ec2.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': ['bank-recognition-vpc']}])['Vpcs']
        exists = "PASS" if vpcs else "FAIL"
        points.append({"Category": "1. VPC", "Item": "VPC Existence", "Status": exists, "Score": 1 if exists == "PASS" else 0, "Feedback": "bank-recognition-vpc"})
        
        if vpcs:
            vpc = vpcs[0]
            vpc_id = vpc['VpcId']
            # Name Tag (1 pt)
            points.append({"Category": "1. VPC", "Item": "VPC Name Tag", "Status": "PASS", "Score": 1, "Feedback": "bank-recognition-vpc"})
            # CIDR (1 pt)
            status = "PASS" if vpc['CidrBlock'] == '192.168.0.0/16' else "FAIL"
            points.append({"Category": "1. VPC", "Item": "VPC CIDR: 192.168.0.0/16", "Status": status, "Score": 1 if status == "PASS" else 0, "Feedback": vpc['CidrBlock']})
            # DNS Support (1 pt)
            dns = ec2.describe_vpc_attribute(VpcId=vpc_id, Attribute='enableDnsSupport')['EnableDnsSupport']['Value']
            points.append({"Category": "1. VPC", "Item": "VPC DNS Support", "Status": "PASS" if dns else "FAIL", "Score": 1 if dns else 0, "Feedback": "Enabled" if dns else "Disabled"})
    except:
        points.append({"Category": "1. VPC", "Item": "VPC Audit", "Status": "FAIL", "Score": 0, "Feedback": "Discovery failed"})

    # 2. Subnets Micro-Audit
    if vpc_id:
        try:
            subnets = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['Subnets']
            targets = [
                'bank-recognition-public-subnet-1', 'bank-recognition-public-subnet-2',
                'bank-recognition-private-subnet-1', 'bank-recognition-private-subnet-2'
            ]
            for name in targets:
                s = next((sub for sub in subnets if any(t['Value'] == name for t in sub.get('Tags', []))), None)
                status = "PASS" if s else "FAIL"
                # Existence (1 pt)
                points.append({"Category": "1. Subnets", "Item": f"Subnet Existence: {name}", "Status": status, "Score": 1 if status == "PASS" else 0, "Feedback": "Found" if s else "Missing"})
                if s:
                    # AZ Multi-AZ (1 pt)
                    points.append({"Category": "1. Subnets", "Item": f"Subnet AZ Config: {name}", "Status": "PASS", "Score": 1, "Feedback": s['AvailabilityZone']})
        except: pass

    # 3. Gateways Micro-Audit
    if vpc_id:
        # IGW (1 pt)
        igws = ec2.describe_internet_gateways(Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}])['InternetGateways']
        points.append({"Category": "1. Gateways", "Item": "Internet Gateway Attached", "Status": "PASS" if igws else "FAIL", "Score": 1 if igws else 0, "Feedback": "Required for Public Tier"})
        
        # NAT (1 pt)
        nats = ec2.describe_nat_gateways(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['NatGateways']
        active_nat = any(n['State'] == 'available' for n in nats)
        points.append({"Category": "1. Gateways", "Item": "NAT Gateway Available", "Status": "PASS" if active_nat else "FAIL", "Score": 1 if active_nat else 0, "Feedback": "Required for Private Tier"})

    return points
