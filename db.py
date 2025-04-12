import psycopg2
import time
from dotenv import load_dotenv
import os

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=env_path)

# Database connection parameters
db_host = os.getenv('PG_HOST')
db_port = os.getenv('PG_PORT')
db_user = os.getenv('PG_USER')
db_pass = os.getenv('PG_PASSWORD')

# Wait for database to be ready
time.sleep(5)

# Create a connection to the database
def get_connection():
    return psycopg2.connect(
        f"host={db_host} port=5432 dbname=accountdb user={db_user} password={db_pass} target_session_attrs=read-write"
    )

# Global connection that can be imported and used by routers
conn = get_connection()
