import requests
import json
import sys

# Get the token from command line
if len(sys.argv) < 2:
    print("Usage: python test_logs_api.py <token>")
    sys.exit(1)

token = sys.argv[1]

# API URL
api_url = "http://localhost:8080"

# Test creating a log
def create_log():
    url = f"{api_url}/logs/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {
        "message": "Test log from script",
        "level": "INFO",
        "category": "TEST",
        "source": "SCRIPT",
        "details": {"test": True},
        "entity_type": "test",
        "entity_id": "1"
    }
    
    response = requests.post(url, headers=headers, json=data)
    print(f"Create log response: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(response.text)

# Test getting logs
def get_logs():
    url = f"{api_url}/logs/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(url, headers=headers)
    print(f"Get logs response: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(response.text)

# Test getting log categories
def get_categories():
    url = f"{api_url}/logs/categories/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(url, headers=headers)
    print(f"Get categories response: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(response.text)

# Test getting log sources
def get_sources():
    url = f"{api_url}/logs/sources/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.get(url, headers=headers)
    print(f"Get sources response: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2))
    else:
        print(response.text)

# Run the tests
if __name__ == "__main__":
    print("Testing logs API...")
    create_log()
    get_logs()
    get_categories()
    get_sources()
