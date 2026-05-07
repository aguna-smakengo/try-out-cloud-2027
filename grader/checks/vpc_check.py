import boto3

def check_vpc_compliance(ec2):
    points = []
    vpc_id = None
    vpc_data = None
    
    # --- 1. VPC CORE FORENSICS ---
    try:
        vpcs = ec2.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': ['bank-recognition-vpc']}])['Vpcs']
        if vpcs:
            vpc_data = vpcs[0]
            vpc_id = vpc_data['VpcId']
    except: pass

    # Points for VPC Core
    points.append({
        "Category": "1. VPC Core", "Item": "VPC Existence", 
        "Status": "PASS" if vpc_id else "FAIL", "Score": 1 if vpc_id else 0, 
        "Expected": "bank-recognition-vpc", "Actual": "Found" if vpc_id else "Missing",
        "Feedback": "Primary networking backbone"
    })
    points.append({
        "Category": "1. VPC Core", "Item": "VPC Name Tag", 
        "Status": "PASS" if vpc_id else "FAIL", "Score": 1 if vpc_id else 0, 
        "Expected": "bank-recognition-vpc", "Actual": "Found" if vpc_id else "Missing",
        "Feedback": "Naming standard compliance"
    })
    
    cidr = vpc_data['CidrBlock'] if vpc_data else "N/A"
    cidr_ok = vpc_data and cidr == '192.168.0.0/16'
    points.append({
        "Category": "1. VPC Core", "Item": "VPC CIDR (192.168.0.0/16)", 
        "Status": "PASS" if cidr_ok else "FAIL", "Score": 1 if cidr_ok else 0, 
        "Expected": "192.168.0.0/16", "Actual": cidr,
        "Feedback": "IP Address range validation"
    })
    
    state = vpc_data['State'] if vpc_data else "N/A"
    state_ok = vpc_data and state == 'available'
    points.append({
        "Category": "1. VPC Core", "Item": "VPC State (Available)", 
        "Status": "PASS" if state_ok else "FAIL", "Score": 1 if state_ok else 0, 
        "Expected": "available", "Actual": state,
        "Feedback": "VPC operational status"
    })

    # --- 2. SUBNETS INSANE FORENSICS ---
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
        cat = f"2. Subnet: {name}"
        points.append({
            "Category": cat, "Item": "Existence", 
            "Status": "PASS" if s else "FAIL", "Score": 1 if s else 0, 
            "Expected": "Exist", "Actual": "Found" if s else "Missing",
            "Feedback": "Subnet provisioning"
        })
        points.append({
            "Category": cat, "Item": "Name Tag Compliance", 
            "Status": "PASS" if s else "FAIL", "Score": 1 if s else 0, 
            "Expected": name, "Actual": name if s else "Missing",
            "Feedback": "Standardized tagging"
        })
        
        act_cidr = s['CidrBlock'] if s else "N/A"
        c_status = "PASS" if s and act_cidr == cidr else "FAIL"
        points.append({
            "Category": cat, "Item": "CIDR Match", 
            "Status": c_status, "Score": 1 if c_status == "PASS" else 0, 
            "Expected": cidr, "Actual": act_cidr,
            "Feedback": "Subnet network range"
        })
        
        act_map = s['MapPublicIpOnLaunch'] if s else "N/A"
        m_status = "PASS" if s and act_map == map_pub else "FAIL"
        points.append({
            "Category": cat, "Item": "MapPublicIp Config", 
            "Status": m_status, "Score": 1 if m_status == "PASS" else 0, 
            "Expected": str(map_pub), "Actual": str(act_map),
            "Feedback": "Public/Private Tier exposure"
        })
        
        act_az = s['AvailabilityZone'] if s else "N/A"
        points.append({
            "Category": cat, "Item": "Availability Zone", 
            "Status": "PASS" if s else "FAIL", "Score": 1 if s else 0, 
            "Expected": "AZ-Assigned", "Actual": act_az,
            "Feedback": "Multi-AZ distribution"
        })

    # --- 3. ROUTE TABLES ---
    rts = []
    if vpc_id:
        try: rts = ec2.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['RouteTables']
        except: pass

    target_rts = [('bank-recognition-public-rt', 'igw-', 2), ('bank-recognition-private-rt', 'nat-', 2)]
    for name, target_pref, exp_assoc in target_rts:
        rt = next((r for r in rts if any(t['Value'] == name for t in r.get('Tags', []))), None)
        cat = f"3. RT: {name}"
        points.append({
            "Category": cat, "Item": "Existence", 
            "Status": "PASS" if rt else "FAIL", "Score": 1 if rt else 0, 
            "Expected": "Exist", "Actual": "Found" if rt else "Missing",
            "Feedback": "Routing logic presence"
        })
        
        has_route = rt and any(target_pref in (route.get('GatewayId', '') or route.get('NatGatewayId', '')) for route in rt['Routes'])
        points.append({
            "Category": cat, "Item": "Route Target Validation", 
            "Status": "PASS" if has_route else "FAIL", "Score": 1 if has_route else 0, 
            "Expected": f"{target_pref}*", "Actual": "Configured" if has_route else "Missing",
            "Feedback": "Gateway routing connectivity"
        })
        
        valid_assocs = [a for a in rt.get('Associations', []) if a.get('SubnetId')] if rt else []
        for i in range(1, exp_assoc + 1):
            a_status = "PASS" if len(valid_assocs) >= i else "FAIL"
            points.append({
                "Category": cat, "Item": f"Subnet Association {i}", 
                "Status": a_status, "Score": 1 if a_status == "PASS" else 0, 
                "Expected": "Associated", "Actual": "Verified" if a_status == "PASS" else "Missing",
                "Feedback": "Traffic mapping to subnets"
            })

    # --- 4. GATEWAYS ---
    igw_attached = False
    nat_available = False
    if vpc_id:
        try:
            igws = ec2.describe_internet_gateways(Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}])['InternetGateways']
            igw_attached = len(igws) > 0
            nats = ec2.describe_nat_gateways(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['NatGateways']
            nat_available = any(n['State'] == 'available' for n in nats)
        except: pass

    points.append({
        "Category": "4. Gateways", "Item": "IGW Existence/Attachment", 
        "Status": "PASS" if igw_attached else "FAIL", "Score": 1 if igw_attached else 0, 
        "Expected": "Attached to VPC", "Actual": "Attached" if igw_attached else "Missing",
        "Feedback": "Public internet connectivity"
    })
    points.append({
        "Category": "4. Gateways", "Item": "NAT Gateway Available", 
        "Status": "PASS" if nat_available else "FAIL", "Score": 1 if nat_available else 0, 
        "Expected": "State: available", "Actual": "Available" if nat_available else "N/A",
        "Feedback": "Private tier outbound connectivity"
    })

    return points
