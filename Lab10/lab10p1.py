import subprocess
import sys

def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Помилка:\n{result.stderr}")
        sys.exit(1)
    return result.stdout.strip()

def main():
    rg_name = "az104-rg-region1"
    location = "swedencentral" 
    template_file = "az104-10-vms-edge-template.json"
    parameters_file = "az104-10-vms-edge-parameters.json"
    admin_password = "AzureLab2026!"

    subprocess.run(f"az group create --name {rg_name} --location {location}", shell=True, capture_output=True)

    deploy_cmd = (
        f"az deployment group create --resource-group {rg_name} "
        f"--template-file {template_file} "
        f"--parameters @{parameters_file} "
        f'--parameters adminPassword="{admin_password}"'
    )
    
    run_command(deploy_cmd)

if __name__ == "__main__":
    main()