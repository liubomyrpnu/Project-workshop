import subprocess
import sys
from datetime import datetime, timedelta

def run_command(command, ignore_error=False):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0 and not ignore_error:
        print(f"Помилка:\n{result.stderr}")
        sys.exit(1)
    return result.stdout.strip()

def main():
    rg_name = "az104-rg11"
    location = "swedencentral"
    template_file = "az104-11-vm-template.json"
    admin_password = "pL9#vXq@2mZ!kR8-"
    admin_email = "dumenchuklub@gmail.com" 
    
    ag_name = "Alert the operations team"
    alert_name = "VM was deleted"

    sub_id = run_command("az account show --query id -o tsv")

    run_command(f"az group create --name {rg_name} --location {location}", ignore_error=True)

    deploy_cmd = (
        f'az deployment group create --resource-group {rg_name} '
        f'--template-file {template_file} '
        f'--parameters adminUsername=localadmin adminPassword="{admin_password}"'
    )
    run_command(deploy_cmd)

    ag_cmd = (
        f'az monitor action-group create --resource-group {rg_name} '
        f'--name "{ag_name}" '
        f'--action email AlertOpsTeam {admin_email}'
    )
    run_command(ag_cmd, ignore_error=True) 
    
    ag_id = run_command(f'az monitor action-group show --resource-group {rg_name} --name "{ag_name}" --query id -o tsv')

    alert_cmd = (
        f'az monitor activity-log alert create '
        f'--name "{alert_name}" '
        f'--resource-group {rg_name} '
        f'--scope /subscriptions/{sub_id} '
        f'--condition category=Administrative and operationName=Microsoft.Compute/virtualMachines/delete '
        f'--action-group "{ag_id}"' 
    )
    run_command(alert_cmd, ignore_error=True)

    run_command("az extension add --name alertsmanagement", ignore_error=True)
    
    now = datetime.now()
    start_time = now.replace(hour=22, minute=0, second=0).strftime('%Y-%m-%d %H:%M:%S')
    end_time = (now + timedelta(days=1)).replace(hour=7, minute=0, second=0).strftime('%Y-%m-%d %H:%M:%S')

    suppress_cmd = (
        f'az monitor alert-processing-rule create '
        f'--name "Planned Maintenance" '
        f'--resource-group {rg_name} '
        f'--rule-type RemoveAllActionGroups '
        f'--scopes "/subscriptions/{sub_id}/resourceGroups/{rg_name}" '
        f'--description "Suppress notifications during planned maintenance." '
        f'--schedule-start-datetime "{start_time}" '
        f'--schedule-end-datetime "{end_time}" '
        f'--schedule-time-zone "FLE Standard Time"' 
    )
    run_command(suppress_cmd, ignore_error=False)

if __name__ == "__main__":
    main()