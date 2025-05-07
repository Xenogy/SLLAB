"""
Simple test script to monitor log files.
"""
import time
import os

def monitor_file(file_path):
    """Monitor a file for changes."""
    print(f"Monitoring file: {file_path}")
    
    # Get initial file size
    try:
        file_size = os.path.getsize(file_path)
    except (FileNotFoundError, OSError):
        file_size = 0
    
    print(f"Initial file size: {file_size}")
    
    while True:
        try:
            # Check current file size
            current_size = os.path.getsize(file_path)
            
            # If file has grown
            if current_size > file_size:
                print(f"File size changed: {file_size} -> {current_size}")
                
                # Read new content
                with open(file_path, 'r') as f:
                    f.seek(file_size)
                    new_content = f.read()
                
                print(f"New content: {new_content}")
                file_size = current_size
            
            time.sleep(1)
        except KeyboardInterrupt:
            print("Monitoring stopped by user")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    monitor_file("test_logs/bot.log")
