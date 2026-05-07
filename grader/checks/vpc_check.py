import boto3

def check_vpc_compliance(ec2):
    points = []
    vpc_id = None
    vpc_data = None
    
    # --- 1. VPC CORE AUDIT ---
    try:
        vpcs = ec2.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': ['bank-recognition-vpc']}])['Vpcs']
        if vpcs:
            vpc_data = vpcs[0]
            vpc_id = vpc_data['VpcId']
    except: pass

    status = "PASS" if vpc_id else "FAIL"
    points.append({"Category": "1. VPC Core", "Item": "VPC Existence", "Status": status, "Score": 1 if status == "PASS" else 0, "Feedback": "bank-recognition-vpc" if vpc_id else "Missing"})
    
    cidr_ok = vpc_data and vpc_data['CidrBlock'] == '192.168.0.0/16'
    points.append({"Category": "1. VPC Core", "Item": "VPC CIDR (192.168.0.0/16)", "Status": "PASS" if cidr_ok else "FAIL", "Score": 1 if cidr_ok else 0, "Feedback": vpc_data['CidrBlock'] if vpc_data else "N/A"})
    
    state_ok = vpc_data and vpc_data['State'] == 'available'
    points.append({"Category": "1. VPC Core", "Item": "VPC State (Available)", "Status": "PASS" if state_ok else "FAIL", "Score": 1 if state_ok else 0, "Feedback": vpc_data['State'] if vpc_data else "N/A"})

    # --- 2. SUBNETS AUDIT ---
    subnets = []
    if vpc_id:
        try: subnets = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['Subnets']
        except: pass
    
    target_subnets = [
        ('bank-recognition-public-subnet-1', '192.168.1.0/24', True),
        ('bank-recognition-public-subnet-2', '192.168.2.0/24', True),
        ('bank-recognition-private-subnet-1', '192.168.3.0/24', False),
        ('bank-recognition-private-subnet-2', '192.168.4.0/24', False)
    ]
    
    for name, cidr, map_pub in target_subnets:
        s = next((sub for sub in subnets if any(t['Value'] == name for t in sub.get('Tags', []))), None)
        
        points.append({"Category": f"2. Subnet: {name}", "Item": "Existence", "Status": "PASS" if s else "FAIL", "Score": 1 if s else 0, "Feedback": "Found" if s else "Missing"})
        
        c_status = "PASS" if s and s['CidrBlock'] == cidr else "FAIL"
        points.append({"Category": f"2. Subnet: {name}", "Item": f"CIDR: {cidr}", "Status": c_status, "Score": 1 if c_status == "PASS" else 0, "Feedback": s['CidrBlock'] if s else "N/A"})
        
        m_status = "PASS" if s and s['MapPublicIpOnLaunch'] == map_pub else "FAIL"
        points.append({"Category": f"2. Subnet: {name}", "Item": f"MapPublicIp: {map_pub}", "Status": m_status, "Score": 1 if m_status == "PASS" else 0, "Feedback": str(s['MapPublicIpOnLaunch']) if s else "N/A"})

    # --- 3. GATEWAYS ---
    igw_attached = False
    nat_available = False
    if vpc_id:
        try:
            igws = ec2.describe_internet_gateways(Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}])['InternetGateways']
            igw_attached = len(igws) > 0
            nats = ec2.describe_nat_gateways(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['NatGateways']
            nat_available = any(n['State'] == 'available' for n in nats)
        except: pass

    points.append({"Category": "4. Gateways", "Item": "IGW Existence/Attachment", "Status": "PASS" if igw_attached else "FAIL", "Score": 1 if igw_attached else 0, "Feedback": "Attached" if igw_attached else "Missing"})
    points.append({"Category": "4. Gateways", "Item": "NAT Gateway Available", "Status": "PASS" if nat_available else "FAIL", "Score": 1 if nat_available else 0, "Feedback": "Found" if nat_available else "Missing"})

    return points
