import boto3

def check_vpc_compliance(ec2):
    points = []
    vpc_id = None
    
    # --- 1. VPC CORE AUDIT ---
    try:
        vpcs = ec2.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': ['bank-recognition-vpc']}])['Vpcs']
        exists = "PASS" if vpcs else "FAIL"
        points.append({"Category": "1. VPC Core", "Item": "VPC: Create/Existence", "Status": exists, "Score": 1 if exists == "PASS" else 0, "Feedback": "bank-recognition-vpc"})
        
        if vpcs:
            vpc = vpcs[0]
            vpc_id = vpc['VpcId']
            points.append({"Category": "1. VPC Core", "Item": "VPC: Name Tag Compliance", "Status": "PASS", "Score": 1, "Feedback": "bank-recognition-vpc"})
            points.append({"Category": "1. VPC Core", "Item": "VPC: CIDR (192.168.0.0/16)", "Status": "PASS" if vpc['CidrBlock'] == '192.168.0.0/16' else "FAIL", "Score": 1, "Feedback": vpc['CidrBlock']})
            points.append({"Category": "1. VPC Core", "Item": "VPC: State (Available)", "Status": "PASS" if vpc['State'] == 'available' else "FAIL", "Score": 1, "Feedback": vpc['State']})
    except:
        points.append({"Category": "1. VPC Core", "Item": "VPC Audit", "Status": "FAIL", "Score": 0, "Feedback": "Discovery failed"})

    if not vpc_id: return points

    # --- 2. SUBNETS INSANE AUDIT ---
    try:
        subnets = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['Subnets']
        
        target_subnets = [
            # (Name, CIDR, MapPublicIp)
            ('bank-recognition-public-subnet-1', '192.168.1.0/24', True),
            ('bank-recognition-public-subnet-2', '192.168.2.0/24', True),
            ('bank-recognition-private-subnet-1', '192.168.3.0/24', False),
            ('bank-recognition-private-subnet-2', '192.168.4.0/24', False)
        ]
        
        for name, cidr, map_pub in target_subnets:
            s = next((sub for sub in subnets if any(t['Value'] == name for t in sub.get('Tags', []))), None)
            status = "PASS" if s else "FAIL"
            points.append({"Category": f"2. Subnet: {name}", "Item": "Create/Existence", "Status": status, "Score": 1 if status == "PASS" else 0, "Feedback": "Resource found" if s else "Missing"})
            
            if s:
                points.append({"Category": f"2. Subnet: {name}", "Item": "Name Tag Compliance", "Status": "PASS", "Score": 1, "Feedback": name})
                # CIDR Match (1 pt)
                c_status = "PASS" if s['CidrBlock'] == cidr else "FAIL"
                points.append({"Category": f"2. Subnet: {name}", "Item": f"CIDR Config: {cidr}", "Status": c_status, "Score": 1 if c_status == "PASS" else 0, "Feedback": s['CidrBlock']})
                # MapPublicIp (1 pt)
                m_status = "PASS" if s['MapPublicIpOnLaunch'] == map_pub else "FAIL"
                points.append({"Category": f"2. Subnet: {name}", "Item": f"MapPublicIp: {map_pub}", "Status": m_status, "Score": 1 if m_status == "PASS" else 0, "Feedback": str(s['MapPublicIpOnLaunch'])})
                # AZ (1 pt)
                points.append({"Category": f"2. Subnet: {name}", "Item": "Availability Zone", "Status": "PASS", "Score": 1, "Feedback": s['AvailabilityZone']})
    except: pass

    # --- 3. ROUTE TABLES INSANE AUDIT ---
    try:
        rts = ec2.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['RouteTables']
        
        target_rts = [
            ('bank-recognition-public-rt', 'igw-', 2), # (Name, RouteTargetPrefix, ExpectedAssocs)
            ('bank-recognition-private-rt', 'nat-', 2)
        ]
        
        for name, target_pref, exp_assoc in target_rts:
            rt = next((r for r in rts if any(t['Value'] == name for t in r.get('Tags', []))), None)
            status = "PASS" if rt else "FAIL"
            points.append({"Category": f"3. RT: {name}", "Item": "Create/Existence", "Status": status, "Score": 1 if status == "PASS" else 0, "Feedback": "Found" if rt else "Missing"})
            
            if rt:
                points.append({"Category": f"3. RT: {name}", "Item": "Name Tag Compliance", "Status": "PASS", "Score": 1, "Feedback": name})
                # Check Routes (1 pt)
                has_route = any(target_pref in (route.get('GatewayId', '') or route.get('NatGatewayId', '')) for route in rt['Routes'])
                points.append({"Category": f"3. RT: {name}", "Item": f"Route Target: {target_pref}*", "Status": "PASS" if has_route else "FAIL", "Score": 1 if has_route else 0, "Feedback": "Found" if has_route else "Missing"})
                # Check Associations (1 pt per assoc)
                assocs = rt.get('Associations', [])
                valid_assocs = [a for a in assocs if a.get('SubnetId')]
                for i in range(1, exp_assoc + 1):
                    a_status = "PASS" if len(valid_assocs) >= i else "FAIL"
                    points.append({"Category": f"3. RT: {name}", "Item": f"Subnet Association {i}", "Status": a_status, "Score": 1 if a_status == "PASS" else 0, "Feedback": valid_assocs[i-1]['SubnetId'] if len(valid_assocs) >= i else "Missing"})
    except: pass

    # --- 4. GATEWAYS INSANE AUDIT ---
    try:
        # IGW
        igws = ec2.describe_internet_gateways(Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}])['InternetGateways']
        points.append({"Category": "4. Gateways", "Item": "IGW: Existence", "Status": "PASS" if igws else "FAIL", "Score": 1, "Feedback": "Found" if igws else "Missing"})
        points.append({"Category": "4. Gateways", "Item": "IGW: VPC Attachment", "Status": "PASS" if igws else "FAIL", "Score": 1, "Feedback": "Attached"})
        
        # NAT
        nats = ec2.describe_nat_gateways(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['NatGateways']
        points.append({"Category": "4. Gateways", "Item": "NAT: Existence", "Status": "PASS" if nats else "FAIL", "Score": 1, "Feedback": "Found" if nats else "Missing"})
        if nats:
            points.append({"Category": "4. Gateways", "Item": "NAT: State (Available)", "Status": "PASS" if nats[0]['State'] == 'available' else "FAIL", "Score": 1, "Feedback": nats[0]['State']})
            points.append({"Category": "4. Gateways", "Item": "NAT: Elastic IP Assigned", "Status": "PASS" if nats[0].get('NatGatewayAddresses') else "FAIL", "Score": 1, "Feedback": "EIP Assigned"})
    except: pass

    return points
