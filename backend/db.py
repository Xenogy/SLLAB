import psycopg2
import time
from dotenv import load_dotenv
import os

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

# Database connection parameters
db_host = os.getenv('PG_HOST', 'localhost')
db_port = os.getenv('PG_PORT', '5432')
db_user = os.getenv('PG_USER', 'postgres')
db_pass = os.getenv('PG_PASSWORD', 'postgres')

# Create a connection to the database
def get_connection():
    try:
        return psycopg2.connect(
            f"host={db_host} port={db_port} dbname=accountdb user={db_user} password={db_pass} target_session_attrs=read-write"
        )
    except Exception as e:
        print(f"Error connecting to database: {e}")
        # Return a mock connection for development/testing
        print("Using mock database connection for development/testing")
        return None

# Global connection that can be imported and used by routers
conn = get_connection()
