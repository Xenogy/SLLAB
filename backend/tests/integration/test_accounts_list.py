import requests
import json
import os

# Get API token from environment variable or use default
API_TOKEN = os.environ.get('API_TOKEN', 'CHANGEME')

# Test the GET endpoint
def test_get_endpoint():
    print("Testing GET endpoint...")
    response = requests.get("http://localhost:8080/accounts/list", params={"token": API_TOKEN})
    if response.status_code == 200:
        data = response.json()
        print(f"Success! Got {len(data['accounts'])} accounts out of {data['total']}")
        print(f"First few accounts: {json.dumps(data['accounts'][:3], indent=2)}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

# Test the POST endpoint
def test_post_endpoint():
    print("\nTesting POST endpoint...")
    payload = {
        "limit": 5,
        "offset": 0,
        "search": None,
        "sort_by": "acc_id",
        "sort_order": "asc",
        "filter_prime": None,
        "filter_lock": None,
        "filter_perm_lock": None
    }
    response = requests.post(f"http://localhost:8080/accounts/list?token={API_TOKEN}", json=payload)
    if response.status_code == 200:
        data = response.json()
        print(f"Success! Got {len(data['accounts'])} accounts out of {data['total']}")
        print(f"First few accounts: {json.dumps(data['accounts'][:3], indent=2)}")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_get_endpoint()
    test_post_endpoint()
