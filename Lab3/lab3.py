import requests
from azure.identity import DefaultAzureCredential

RG_NAME = "az104-rg3"
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

def get_arm_template():
    return {
        "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
        "contentVersion": "1.0.0.0",
        "parameters": {
            "disk_name": {"type": "string"},
            "location": {"type": "string", "defaultValue": "[resourceGroup().location]"},
            "sku_name": {"type": "string", "defaultValue": "Standard_LRS"},
            "diskSizeGb": {"type": "int", "defaultValue": 32}
        },
        "resources": [
            {
                "type": "Microsoft.Compute/disks",
                "apiVersion": "2023-04-02",
                "name": "[parameters('disk_name')]",
                "location": "[parameters('location')]",
                "sku": {
                    "name": "[parameters('sku_name')]"
                },
                "properties": {
                    "creationData": {
                        "createOption": "Empty"
                    },
                    "diskSizeGB": "[parameters('diskSizeGb')]"
                }
            }
        ]
    }

def deploy_disk_via_template(sub_id, headers, disk_name, sku_name="Premium_LRS"):
    deployment_name = f"deploy-{disk_name}"
    deploy_url = f"https://management.azure.com/subscriptions/{sub_id}/resourcegroups/{RG_NAME}/providers/Microsoft.Resources/deployments/{deployment_name}?api-version=2021-04-01"
    
    payload = {
        "properties": {
            "mode": "Incremental",
            "template": get_arm_template(),
            "parameters": {
                "disk_name": {"value": disk_name},
                "sku_name": {"value": sku_name}
            }
        }
    }
    
    requests.put(deploy_url, headers=headers, json=payload)

def main():
    headers = get_arm_headers()
    sub_id = get_subscription_id(headers)
    if not sub_id:
        return

    rg_url = f"https://management.azure.com/subscriptions/{sub_id}/resourcegroups/{RG_NAME}?api-version=2021-04-01"
    rg_payload = {"location": LOCATION}
    res = requests.put(rg_url, headers=headers, json=rg_payload)
    if res.status_code not in [200, 201]:
        return

    deploy_disk_via_template(sub_id, headers, "az104-disk1")
    deploy_disk_via_template(sub_id, headers, "az104-disk2")
    deploy_disk_via_template(sub_id, headers, "az104-disk3")
    deploy_disk_via_template(sub_id, headers, "az104-disk4")
    deploy_disk_via_template(sub_id, headers, "az104-disk5", sku_name="StandardSSD_LRS")

if __name__ == "__main__":
    main()