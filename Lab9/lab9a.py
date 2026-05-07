import subprocess
import sys

def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Помилка:\n{result.stderr}")
        sys.exit(1)
    return result.stdout.strip()

def main():
    rg_name = "az104-rg9"
    location = "westeurope"
    asp_name = "ASP-az104rg9-8fa0"
    app_name = "az104-webapp-12345" 

    run_command(f"az group create --name {rg_name} --location {location}")
    run_command(f"az appservice plan create -g {rg_name} -n {asp_name} --location {location} --sku S1 --is-linux")
    run_command(f"az webapp create -g {rg_name} -p {asp_name} -n {app_name} --runtime \"PHP|8.2\"")

    run_command(f"az webapp deployment slot create -g {rg_name} -n {app_name} --slot staging")

    run_command(f"az webapp deployment source config -g {rg_name} -n {app_name} --slot staging --repo-url https://github.com/Azure-Samples/php-docs-hello-world --branch master --manual-integration")

    run_command(f"az webapp deployment slot swap -g {rg_name} -n {app_name} --slot staging --target-slot production")

    print(f"Головна: https://{app_name}.azurewebsites.net")

if __name__ == "__main__":
    main()