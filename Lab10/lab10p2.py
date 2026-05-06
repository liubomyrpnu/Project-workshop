import subprocess
import sys
import json
import os

def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Помилка:\n{result.stderr}")
        sys.exit(1)
    return result.stdout.strip()

def main():
    rg_name = "az104-rg-region1"
    location = "swedencentral"
    vault_name = "az104-rsv-region1"
    vm_name = "az104-10-vm0"
    storage_account_name = "az104storagedumen123" 

    subprocess.run(f"az backup vault create --resource-group {rg_name} --name {vault_name} --location {location}", shell=True, capture_output=True)

    enable_cmd = f"az backup protection enable-for-vm --resource-group {rg_name} --vault-name {vault_name} --vm {vm_name} --policy-name DefaultPolicy"
    subprocess.run(enable_cmd, shell=True, capture_output=True)

    backup_cmd = (
        f"az backup protection backup-now "
        f"--resource-group {rg_name} "
        f"--vault-name {vault_name} "
        f"--container-name {vm_name} "
        f"--item-name {vm_name} "
        f"--retain-until 28-05-2026 "
        f"--backup-management-type AzureIaasVM"
    )
    subprocess.run(backup_cmd, shell=True, capture_output=True)

    subprocess.run(f"az storage account create --name {storage_account_name} --resource-group {rg_name} --location {location} --sku Standard_LRS", shell=True, capture_output=True)
    
    storage_id = run_command(f"az storage account show --name {storage_account_name} --resource-group {rg_name} --query id -o tsv")
    vault_id = run_command(f"az backup vault show --name {vault_name} --resource-group {rg_name} --query id -o tsv")

    logs_config = [
        {"category": "AzureBackupReport", "enabled": True},
        {"category": "AddonAzureBackupJobs", "enabled": True},
        {"category": "AddonAzureBackupAlerts", "enabled": True},
        {"category": "AzureSiteRecoveryJobs", "enabled": True},
        {"category": "AzureSiteRecoveryEvents", "enabled": True}
    ]
    
    with open("logs_config.json", "w") as f:
        json.dump(logs_config, f)

    run_command(f"az monitor diagnostic-settings create --name 'Logs-and-Metrics-to-storage' --resource {vault_id} --storage-account {storage_id} --logs @logs_config.json")

    if os.path.exists("logs_config.json"):
        os.remove("logs_config.json")

if __name__ == "__main__":
    main()