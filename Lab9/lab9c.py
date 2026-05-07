import subprocess
import sys

def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Помилка:\n{result.stderr}")
        sys.exit(1)
    return result.stdout.strip().strip('"')

def main():
    rg_name = "az104-rg9c"
    location = "westeurope"
    env_name = "my-environment"
    app_name = "my-app"

    subprocess.run(f"az group create --name {rg_name} --location {location}", shell=True, capture_output=True)

    run_command(f"az containerapp env create --name {env_name} --resource-group {rg_name} --location {location}")

    app_cmd = (
        f"az containerapp create --name {app_name} --resource-group {rg_name} "
        f"--environment {env_name} --image mcr.microsoft.com/azuredocs/containerapps-helloworld:latest "
        f"--target-port 80 --ingress external"
    )
    run_command(app_cmd)

    fqdn = run_command(f"az containerapp show --name {app_name} --resource-group {rg_name} --query properties.configuration.ingress.fqdn --output tsv")

    print(f"https://{fqdn}")

if __name__ == "__main__":
    main()