import requests
import json
import time
import os

def get_token():
    """Get an authentication token."""
    print("Getting authentication token...")
    
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

def test_direct_log_api():
    """Test the log API endpoint with direct database insertion."""
    print("Testing direct log API endpoint...")
    
    # Get a token
    token = get_token()
    if not token:
        print("Could not get authentication token. Exiting.")
        return
    
    # Create a log entry with async_log=false to force synchronous logging
    log_data = {
        "message": "Test log entry from test_direct_log.py",
        "level": "INFO",
        "category": "system",
        "source": "backend",
        "details": {"test": True, "timestamp": time.time(), "async": False},
        "entity_type": "test",
        "entity_id": "123",
        "user_id": 1,
        "owner_id": 1,
        "async_log": False  # Force synchronous logging
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
        
        # Check the database directly
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
    else:
        print("Failed to create log.")

if __name__ == "__main__":
    test_direct_log_api()
