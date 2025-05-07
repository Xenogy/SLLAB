import requests
import json
import time
import os

def get_token():
    """Get an authentication token."""
    print("Getting authentication token...")
    
    # Try to get a token from the environment
    token = os.environ.get("API_TOKEN")
    if token:
        print("Using token from environment variable.")
        return token
    
    # Try with admin credentials
    print("Trying to log in with admin credentials...")
    
    # Create form data for OAuth2 password flow
    data = {
        "username": "admin",
        "password": "admin123!"
    }
    
    # Send the request
    response = requests.post(
        "http://localhost:8080/auth/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    # Check if login was successful
    if response.status_code == 200:
        token_data = response.json()
        print(f"Login successful!")
        return token_data.get("access_token")
    else:
        print(f"Login failed: {response.text}")
        return None

def check_database():
    """Check the database directly."""
    print("\nChecking database directly...")
    
    # Check logs count
    try:
        import psycopg2
        
        # Connect to the database
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="accountdb",
            user="ps_user",
            password="BALLS123"
        )
        
        # Create a cursor
        cursor = conn.cursor()
        
        # Check logs count
        cursor.execute("SELECT COUNT(*) FROM logs")
        count = cursor.fetchone()[0]
        print(f"Found {count} logs in the database")
        
        # Check the most recent logs
        cursor.execute("SELECT id, timestamp, message, level_id FROM logs ORDER BY id DESC LIMIT 5")
        logs = cursor.fetchall()
        
        if logs:
            print("Most recent logs:")
            for log in logs:
                print(f"  - ID: {log[0]}, Timestamp: {log[1]}, Message: {log[2]}, Level: {log[3]}")
        else:
            print("No logs found in the database")
        
        # Close the cursor and connection
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error checking database: {e}")

def test_log_api():
    """Test the log API endpoint."""
    print("Testing log API endpoint...")
    
    # Get a token
    token = get_token()
    if not token:
        print("Could not get authentication token. Exiting.")
        return
    
    # Create a log entry
    log_data = {
        "message": "Test log entry from test_log_thread.py",
        "level": "INFO",
        "category": "system",
        "source": "backend",
        "details": {"test": True, "timestamp": time.time()},
        "entity_type": "test",
        "entity_id": "123",
        "user_id": 1,
        "owner_id": 1
    }
    
    # Send the request with token
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    response = requests.post("http://localhost:8080/logs/", json=log_data, headers=headers)
    
    # Print the response
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Check if the log was created
    if response.status_code == 200:
        print("Log created successfully!")
        
        # Check the database to see if the log was actually stored
        print("\nChecking if log was stored in database...")
        check_logs_response = requests.get(
            "http://localhost:8080/logs/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if check_logs_response.status_code == 200:
            logs_data = check_logs_response.json()
            print(f"Found {logs_data.get('total', 0)} logs in the database via API.")
            
            # Print the first few logs
            logs = logs_data.get("logs", [])
            if logs:
                print("Latest logs via API:")
                for log in logs[:3]:  # Show up to 3 logs
                    print(f"  - {log.get('message')} ({log.get('level')}, {log.get('timestamp')})")
            else:
                print("No logs found in the database via API.")
        else:
            print(f"Failed to check logs: {check_logs_response.status_code} - {check_logs_response.text}")
    else:
        print("Failed to create log.")
    
    # Check the database directly
    check_database()
    
    # Wait a bit to see if the background thread processes the log
    print("\nWaiting 5 seconds to see if the background thread processes the log...")
    time.sleep(5)
    
    # Check the database again
    check_database()

if __name__ == "__main__":
    test_log_api()
