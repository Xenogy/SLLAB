import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add the parent directory to sys.path
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)

# Import the config module
try:
    from config import Config
except ImportError:
    # If we're running in the Docker container, the path might be different
    import sys
    import logging
    logger = logging.getLogger('alembic')
    logger.info(f"Current sys.path: {sys.path}")
    logger.info(f"Trying to import Config from absolute path")

    # Try with absolute import
    from config import Config

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set the database URL in the config
try:
    db_url = f'postgresql://{Config.DB_USER}:{Config.DB_PASS}@{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}'
    config.set_main_option('sqlalchemy.url', db_url)
    logger = logging.getLogger('alembic')
    logger.info(f"Database URL set to: postgresql://{Config.DB_USER}:***@{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_NAME}")
except Exception as e:
    logger = logging.getLogger('alembic')
    logger.error(f"Error setting database URL: {e}")

    # Fallback to environment variables
    db_user = os.getenv('PG_USER', 'postgres')
    db_pass = os.getenv('PG_PASSWORD', 'postgres')
    db_host = os.getenv('PG_HOST', 'postgres')
    db_port = os.getenv('PG_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'accountdb')

    db_url = f'postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}'
    config.set_main_option('sqlalchemy.url', db_url)
    logger.info(f"Using fallback database URL: postgresql://{db_user}:***@{db_host}:{db_port}/{db_name}")

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
