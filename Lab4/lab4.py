import json
import requests
import time
from azure.identity import DefaultAzureCredential

RG_NAME = "az104-rg4"
LOCATION = "eastus"

def get_arm_headers():
    credential = DefaultAzureCredential()
    token = credential.get_token('https://management.azure.com/.default').token
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

def get_subscription_id(headers):
    sub_url = "https://management.azure.com/subscriptions?api-version=2020-01-01"
    response = requests.get(sub_url, headers=headers)
    if response.status_code == 200:
        subs = response.json().get('value', [])
        if subs:
            return subs[0].get('subscriptionId')
    return None

def main():
    headers = get_arm_headers()
    sub_id = get_subscription_id(headers)
    if not sub_id:
        print("Помилка: підписку не знайдено.")
        return

    base_url = f"https://management.azure.com/subscriptions/{sub_id}/resourceGroups/{RG_NAME}"

    rg_url = f"{base_url}?api-version=2021-04-01"
    requests.put(rg_url, headers=headers, json={"location": LOCATION})

    asg_url = f"{base_url}/providers/Microsoft.Network/applicationSecurityGroups/asg-web?api-version=2023-04-01"
    res_asg = requests.put(asg_url, headers=headers, json={"location": LOCATION})
    if res_asg.status_code not in [200, 201]:
        print(f"Помилка створення ASG: {res_asg.text}")
        return
    asg_id = res_asg.json().get('id')

    nsg_url = f"{base_url}/providers/Microsoft.Network/networkSecurityGroups/myNSGSecure?api-version=2023-04-01"
    nsg_payload = {
        "location": LOCATION,
        "properties": {
            "securityRules": [
                {
                    "name": "AllowASG",
                    "properties": {
                        "protocol": "Tcp",
                        "sourcePortRange": "*",
                        "destinationPortRanges": ["80", "443"],
                        "sourceApplicationSecurityGroups": [{"id": asg_id}],
                        "destinationAddressPrefix": "*",
                        "access": "Allow",
                        "priority": 100,
                        "direction": "Inbound"
                    }
                },
                {
                    "name": "DenyInternetOutbound",
                    "properties": {
                        "protocol": "*",
                        "sourcePortRange": "*",
                        "destinationPortRange": "*",
                        "sourceAddressPrefix": "*",
                        "destinationAddressPrefix": "Internet",
                        "access": "Deny",
                        "priority": 4096,
                        "direction": "Outbound"
                    }
                }
            ]
        }
    }
    res_nsg = requests.put(nsg_url, headers=headers, json=nsg_payload)
    if res_nsg.status_code not in [200, 201]:
        print(f"Помилка створення NSG: {res_nsg.text}")
        return
    nsg_id = res_nsg.json().get('id')

    vnet1_url = f"{base_url}/providers/Microsoft.Network/virtualNetworks/CoreServicesVnet?api-version=2023-04-01"
    vnet1_payload = {
        "location": LOCATION,
        "properties": {
            "addressSpace": {"addressPrefixes": ["10.20.0.0/16"]},
            "subnets": [
                {
                    "name": "SharedServicesSubnet",
                    "properties": {
                        "addressPrefix": "10.20.10.0/24",
                        "networkSecurityGroup": {"id": nsg_id}
                    }
                },
                {
                    "name": "DatabaseSubnet",
                    "properties": {"addressPrefix": "10.20.20.0/24"}
                }
            ]
        }
    }
    res_v1 = requests.put(vnet1_url, headers=headers, json=vnet1_payload)
    if res_v1.status_code not in [200, 201]:
        print(f"Помилка створення VNet1: {res_v1.text}")

    try:
        with open('az104-04-template.json', 'r') as f:
            template_data = json.load(f)
        with open('az104-04-parameters.json', 'r') as f:
            parameters_data = json.load(f)

        deploy_url = f"{base_url}/providers/Microsoft.Resources/deployments/Task2Deployment?api-version=2021-04-01"
        deploy_payload = {
            "properties": {
                "template": template_data,
                "parameters": parameters_data['parameters'],
                "mode": "Incremental"
            }
        }
        res_deploy = requests.put(deploy_url, headers=headers, json=deploy_payload)
        if res_deploy.status_code not in [200, 201]:
            print(f"Помилка деплою через шаблон (Task 2): {res_deploy.text}")
    except FileNotFoundError:
        print("Помилка: файли template.json або parameters.json не знайдено.")

    pub_dns_url = f"{base_url}/providers/Microsoft.Network/dnsZones/contoso.com?api-version=2018-05-01"
    requests.put(pub_dns_url, headers=headers, json={"location": "global"})
    
    pub_record_url = f"{base_url}/providers/Microsoft.Network/dnsZones/contoso.com/A/www?api-version=2018-05-01"
    requests.put(pub_record_url, headers=headers, json={"properties": {"TTL": 3600, "ARecords": [{"ipv4Address": "10.1.1.4"}]}})

    priv_dns_url = f"{base_url}/providers/Microsoft.Network/privateDnsZones/private.contoso.com?api-version=2020-06-01"
    requests.put(priv_dns_url, headers=headers, json={"location": "global"})

    vnet2_url = f"{base_url}/providers/Microsoft.Network/virtualNetworks/ManufacturingVnet?api-version=2023-04-01"
    
    for attempt in range(12):
        res_v2 = requests.get(vnet2_url, headers=headers)
        if res_v2.status_code == 200:
            vnet2_id = res_v2.json().get('id')
            
            link_url = f"{base_url}/providers/Microsoft.Network/privateDnsZones/private.contoso.com/virtualNetworkLinks/manufacturing-link?api-version=2020-06-01"
            requests.put(link_url, headers=headers, json={"location": "global", "properties": {"registrationEnabled": False, "virtualNetwork": {"id": vnet2_id}}})

            priv_record_url = f"{base_url}/providers/Microsoft.Network/privateDnsZones/private.contoso.com/A/sensorvm?api-version=2020-06-01"
            requests.put(priv_record_url, headers=headers, json={"properties": {"ttl": 3600, "aRecords": [{"ipv4Address": "10.1.1.4"}]}})
            
            break
        time.sleep(5)
    else:
        print(f"Помилка: ManufacturingVnet не створено за відведений час. Відповідь сервера: {res_v2.text if 'res_v2' in locals() else 'Немає відповіді'}")

if __name__ == "__main__":
    main()