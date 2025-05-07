import requests

# Disable SSL verification warnings
requests.packages.urllib3.disable_warnings()
# Example usage
token = "accdb@pam!d59ce482-4a9e-43a9-ae3d-2a73066e7019=1ad5b026-408a-4f06-bbc1-89b386fd06c0"

def get_vm_ip(node: str, vmid: int, token: str) -> str:
    url = f"https://10.0.0.30:8006/api2/json/nodes/{node}/qemu/{vmid}/agent/network-get-interfaces"
    headers = {
        'Authorization': f'PVEAPIToken={token}'
    }

    try:
        response = requests.get(url, headers=headers, verify=False)
        data = response.json()
        print(data)
        # Parse the response to find IPv4 address
        if 'data' in data and 'result' in data['data']:
            for interface in data['data']['result']:
                if 'ip-addresses' in interface:
                    for ip in interface['ip-addresses']:
                        if ip['ip-address-type'] == 'ipv4' and not ip['ip-address'].startswith('127.'):
                            return ip['ip-address']
        return None
    except Exception as e:
        print(f"Error getting IP address: {e}")
        return None



def ip(vmid: int) -> str:
    return get_vm_ip("gpu1", vmid, token)