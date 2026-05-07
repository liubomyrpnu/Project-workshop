import subprocess
import json
import sys

def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Помилка:\n{result.stderr}")
        sys.exit(1)

def get_json_output(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None

def main():
    rg_name = "az104-rg6"
    lb_name = "az104-lb"
    pip_name = "az104-06-pip4"
    
    run_command(f"az network public-ip create -g {rg_name} -n {pip_name} --sku Standard")
    run_command(f"az network lb create -g {rg_name} -n {lb_name} --sku Standard --public-ip-address {pip_name} --frontend-ip-name myFrontEnd --backend-pool-name az104-be")
    run_command(f"az network lb probe create -g {rg_name} --lb-name {lb_name} -n myHealthProbe --protocol tcp --port 80")
    run_command(f"az network lb rule create -g {rg_name} --lb-name {lb_name} -n myHTTPRule --protocol tcp --frontend-port 80 --backend-port 80 --frontend-ip-name myFrontEnd --backend-pool-name az104-be --probe-name myHealthProbe --disable-outbound-snat true")
    
    servers = ["vm0", "vm1"]
    for vm in servers:
        vm_info = get_json_output(f"az vm show -g {rg_name} -n {vm}")
        if vm_info and 'networkProfile' in vm_info:
            nic_id = vm_info['networkProfile']['networkInterfaces'][0]['id']
            nic_name = nic_id.split('/')[-1]
            nic_info = get_json_output(f"az network nic show -g {rg_name} -n {nic_name}")
            if nic_info and 'ipConfigurations' in nic_info:
                ipconf_name = nic_info['ipConfigurations'][0]['name']
                run_command(f"az network nic ip-config address-pool add --address-pool az104-be --ip-config-name {ipconf_name} --nic-name {nic_name} -g {rg_name} --lb-name {lb_name}")

if __name__ == "__main__":
    main()