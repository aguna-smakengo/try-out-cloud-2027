import boto3

def check_vpc_compliance(ec2):
    points = []
    vpc_id = None
    
    # 1. VPC Basic Check
    try:
        vpcs = ec2.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': ['bank-recognition-vpc']}])['Vpcs']
        status = "PASS" if vpcs else "FAIL"
        vpc_id = vpcs[0]['VpcId'] if vpcs else None
        points.append({
            "Category": "1. Networking", "Item": "VPC Existence",
            "Status": status, "Score": 10 if status == "PASS" else 0,
            "Expected": "bank-recognition-vpc", "Actual": vpcs[0].get('VpcId', 'Not Found') if vpcs else "Not Found",
            "Feedback": "VPC must exist with Name tag 'bank-recognition-vpc'"
        })
        
        if vpcs:
            cidr = vpcs[0]['CidrBlock']
            status = "PASS" if cidr == '192.168.0.0/16' else "FAIL"
            points.append({
                "Category": "1. Networking", "Item": "VPC CIDR Block",
                "Status": status, "Score": 10 if status == "PASS" else 0,
                "Expected": "192.168.0.0/16", "Actual": cidr,
                "Feedback": "VPC must use the 192.168.0.0/16 network range"
            })
    except Exception as e:
        points.append({"Category": "1. Networking", "Item": "VPC Discovery", "Status": "FAIL", "Score": 0, "Feedback": str(e)})

    # 2. Subnets Check
    if vpc_id:
        try:
            subnets = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['Subnets']
            
            check_list = [
                ('bank-recognition-public-subnet-1', 'Public Tier'),
                ('bank-recognition-public-subnet-2', 'Public Tier'),
                ('bank-recognition-private-subnet-1', 'Private Tier'),
                ('bank-recognition-private-subnet-2', 'Private Tier')
            ]
            
            for tag_name, tier in check_list:
                s = next((sub for sub in subnets if any(t['Value'] == tag_name for t in sub.get('Tags', []))), None)
                status = "PASS" if s else "FAIL"
                points.append({
                    "Category": "1. Networking", "Item": f"Subnet: {tag_name}",
                    "Status": status, "Score": 5 if status == "PASS" else 0,
                    "Expected": f"Exist in {tier}", "Actual": s['SubnetId'] if s else "Not Found",
                    "Feedback": f"Mandatory {tier} segmentation"
                })
        except: pass

    # 3. NAT & IGW
    if vpc_id:
        try:
            nats = ec2.describe_nat_gateways(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['NatGateways']
            active_nat = any(n['State'] == 'available' for n in nats)
            points.append({
                "Category": "1. Networking", "Item": "NAT Gateway (High Availability)",
                "Status": "PASS" if active_nat else "FAIL", "Score": 15 if active_nat else 0,
                "Expected": "Available", "Actual": "Found" if active_nat else "Missing",
                "Feedback": "Required for private subnet outbound traffic"
            })
            
            igws = ec2.describe_internet_gateways(Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}])['InternetGateways']
            points.append({
                "Category": "1. Networking", "Item": "Internet Gateway",
                "Status": "PASS" if igws else "FAIL", "Score": 10 if igws else 0,
                "Expected": "Attached", "Actual": "Attached" if igws else "Detached",
                "Feedback": "Required for public subnet inbound traffic"
            })
        except: pass

    return points
