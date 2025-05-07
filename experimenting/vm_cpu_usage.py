import requests

# Disable SSL verification warnings (equivalent to curl's -k flag)
requests.packages.urllib3.disable_warnings()

url = "https://10.0.0.30:8006/api2/json/nodes/gpu1/qemu/5001/status/current"
headers = {
    'Authorization': 'PVEAPIToken=accdb@pam!d59ce482-4a9e-43a9-ae3d-2a73066e7019=1ad5b026-408a-4f06-bbc1-89b386fd06c0'
}

# Make the request (verify=False is equivalent to curl's -k flag)
def usage():
    return requests.get(url, headers=headers, verify=False).json()