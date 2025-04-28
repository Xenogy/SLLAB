"""
Initialize Row-Level Security (RLS) in the database.
This script should be run after the database schema has been created.
"""

import psycopg2
import os
import time
import logging
from pathlib import Path
from config import Config

# Configure logging
logger = logging.getLogger(__name__)

def init_rls():
    """Initialize Row-Level Security in the database."""
    logger.info("Initializing Row-Level Security...")

    # Make sure we have a logs directory
    os.makedirs("logs", exist_ok=True)

    # Wait for the database to be ready
    max_retries = 30  # Increase retries
    retry_interval = 5  # Longer interval between retries

    for i in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                dbname=Config.DB_NAME,
                user=Config.DB_USER,
                password=Config.DB_PASS,
                target_session_attrs="read-write"
            )
            break
        except Exception as e:
            logger.warning(f"Error connecting to database (attempt {i+1}/{max_retries}): {e}")
            if i < max_retries - 1:
                logger.info(f"Retrying in {retry_interval} seconds...")
                time.sleep(retry_interval)
            else:
                logger.error("Failed to connect to the database after multiple attempts.")
                return

    try:
        cursor = conn.cursor()

        # Get the SQL scripts
        sql_dir = Path(__file__).parent / "db" / "sql"
        rls_policies_path = sql_dir / "rls_policies.sql"
        rls_views_path = sql_dir / "rls_views.sql"

        # Execute the RLS policies script
        logger.info("Applying RLS policies...")
        with open(rls_policies_path, "r") as f:
            rls_policies_sql = f.read()
            cursor.execute(rls_policies_sql)

        # Execute the RLS views script
        logger.info("Creating RLS views...")
        with open(rls_views_path, "r") as f:
            rls_views_sql = f.read()
            cursor.execute(rls_views_sql)

        # Grant permissions to the database user
        logger.info("Granting permissions...")
        cursor.execute(f"""
            GRANT ALL ON TABLE public.accounts TO {Config.DB_USER};
            GRANT ALL ON TABLE public.hardware TO {Config.DB_USER};
            GRANT ALL ON TABLE public.cards TO {Config.DB_USER};
            GRANT ALL ON TABLE public.vms TO {Config.DB_USER};
            GRANT ALL ON TABLE public.proxmox_nodes TO {Config.DB_USER};
            GRANT ALL ON TABLE public.accounts_with_rls TO {Config.DB_USER};
            GRANT ALL ON TABLE public.hardware_with_rls TO {Config.DB_USER};
            GRANT ALL ON TABLE public.cards_with_rls TO {Config.DB_USER};
            GRANT ALL ON TABLE public.vms_with_rls TO {Config.DB_USER};
            GRANT ALL ON TABLE public.proxmox_nodes_with_rls TO {Config.DB_USER};
        """)

        conn.commit()
        logger.info("Row-Level Security initialized successfully.")

    except Exception as e:
        try:
            conn.rollback()
        except:
            pass
        import traceback
        error_msg = f"Error initializing Row-Level Security: {e}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())

        # Log the error to a file
        try:
            with open("logs/rls_init_error.log", "a") as f:
                f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {error_msg}\n")
                f.write(traceback.format_exc())
                f.write("\n\n")
        except Exception as log_error:
            logger.error(f"Error writing to log file: {log_error}")
    finally:
        try:
            cursor.close()
        except:
            pass
        try:
            conn.close()
        except:
            pass

if __name__ == "__main__":
    init_rls()
