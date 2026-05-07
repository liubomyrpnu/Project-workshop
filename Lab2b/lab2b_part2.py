import subprocess
import json
import sys
import random
import string

def run_az_command(cmd, return_json=True, ignore_errors=False):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)
    if result.returncode != 0:
        if ignore_errors:
            return result.stderr
        print(f"Помилка: {result.stderr}")
        sys.exit(1)
    if return_json and result.stdout.strip():
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return result.stdout.strip()
    return result.stdout.strip()

sub_info = run_az_command(["az", "account", "show"])
sub_id = sub_info.get("id")

if not sub_id:
    print("Помилка: Не вдалося отримати ID підписки.")
    sys.exit(1)

rg_name = "az104-rg2"
location = "eastus"

suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
sa_name = f"storage{suffix}"

run_az_command([
    "az", "storage", "account", "create",
    "--name", sa_name,
    "--resource-group", rg_name,
    "--location", location,
    "--sku", "Standard_LRS",
    "--subscription", sub_id
], return_json=False)

sa_info = run_az_command([
    "az", "storage", "account", "show", 
    "--name", sa_name, 
    "--resource-group", rg_name,
    "--subscription", sub_id
])

delete_attempt = run_az_command([
    "az", "group", "delete",
    "--name", rg_name,
    "--yes",
    "--subscription", sub_id
], return_json=False, ignore_errors=True)

if "ScopeLocked" not in delete_attempt:
    print(f"Помилка: Видалення не було заблоковано. Деталі: {delete_attempt}")