import os
import time
from fastapi import Depends, FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager

# Use absolute imports instead of relative imports
from dependencies import get_query_token, get_token_header
from routers import accounts, cards, hardware, steam_auth, account_status, auth, upload, vms, proxmox_nodes, monitoring, vm_access, windows_vm_agent, settings, timeseries, farmlabs, logs, ban_check, downloads
#from init_rls import init_rls
from fix_ownership import fix_ownership
from config import Config
from error_handling import setup_error_handling
from error_handling.reporting import log_error, report_error
from middleware.rate_limiting import RateLimitMiddleware
from middleware.timeout import TimeoutMiddleware
from middleware.size_limit import SizeLimitMiddleware
from monitoring import init_monitoring, shutdown_monitoring, TracingMiddleware
from timeseries import init_collector, init_aggregator, shutdown_collector, shutdown_aggregator

# Configure logging
# Create logs directory if it doesn't exist
os.makedirs(os.path.dirname(Config.LOG_FILE), exist_ok=True)

# Set up handlers
handlers = [logging.StreamHandler()]

# Add file handler with rotation if enabled
if Config.LOG_ROTATION:
    from logging.handlers import RotatingFileHandler
    handlers.append(
        RotatingFileHandler(
            Config.LOG_FILE,
            maxBytes=Config.LOG_MAX_SIZE,
            backupCount=Config.LOG_BACKUP_COUNT
        )
    )
else:
    handlers.append(logging.FileHandler(Config.LOG_FILE))

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format=Config.LOG_FORMAT,
    handlers=handlers
)
logger = logging.getLogger(__name__)

# Log configuration
Config.log_config()

# Startup event to initialize RLS, monitoring, and database improvements
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize on startup
    logger.info("Initializing application...")
    try:
        # Make sure logs directory exists
        os.makedirs("logs", exist_ok=True)

        # Initialize monitoring
        init_monitoring()

        # Initialize log storage system
        logger.info("Initializing log storage system...")
        from utils.log_utils import init_logging as init_log_storage
        init_log_storage()
        logger.info("Log storage system initialized")

        # Wait for database and initialize connection pool
        logger.info("Waiting for database and initializing connection pool...")
        from db import wait_for_database, initialize_connection_pool
        if not wait_for_database(max_retries=30, retry_interval=2):
            logger.warning("Database not available after waiting, will retry in background")
        else:
            # Initialize connection pool
            if not initialize_connection_pool():
                logger.warning("Failed to initialize connection pool, will retry in background")

        # Initialize database monitoring and health checks
        logger.info("Initializing database monitoring and health checks...")
        from db.monitoring import init_monitoring as init_db_monitoring
        from db.health_checks import init_health_checks
        init_db_monitoring()
        init_health_checks()
        logger.info("Database monitoring and health checks initialized")

        # Initialize timeseries collection and aggregation
        logger.info("Initializing timeseries collection and aggregation...")
        init_collector()
        init_aggregator()
        logger.info("Timeseries collection and aggregation initialized")

        # Run database improvements
        logger.info("Running database improvements...")
        from db.startup_improvements import run_startup_improvements
        improvement_results = run_startup_improvements()
        logger.info(f"Database improvements completed: {improvement_results}")

        # Fix ownership for existing accounts
        logger.info("Fixing ownership for existing accounts...")
        success = fix_ownership(max_retries=5, retry_interval=2)
        if success:
            logger.info("Ownership fixed successfully")
        else:
            logger.warning("Failed to fix ownership, will retry later")
    except Exception as e:
        error_msg = f"Error during application initialization: {e}"

        # Log the error with structured logging
        log_error(e, extra={"phase": "startup", "component": "initialization"})

        # Report the error to configured services
        report_error(e, extra={"phase": "startup", "component": "initialization"})

        # Also print to console for Docker logs
        print(error_msg)

    yield

    # Cleanup on shutdown
    logger.info("Shutting down...")

    # Shutdown database monitoring and health checks
    try:
        from db.monitoring import shutdown_monitoring as shutdown_db_monitoring
        from db.health_checks import shutdown_health_checks
        shutdown_db_monitoring()
        shutdown_health_checks()
        logger.info("Database monitoring and health checks shutdown")
    except Exception as e:
        logger.error(f"Error shutting down database monitoring and health checks: {e}")

    # Shutdown log storage system
    try:
        from utils.log_utils import shutdown_logging as shutdown_log_storage
        shutdown_log_storage()
        logger.info("Log storage system shutdown")
    except Exception as e:
        logger.error(f"Error shutting down log storage system: {e}")

    # Shutdown timeseries collection and aggregation
    try:
        logger.info("Shutting down timeseries collection and aggregation...")
        shutdown_collector()
        shutdown_aggregator()
        logger.info("Timeseries collection and aggregation shutdown")
    except Exception as e:
        logger.error(f"Error shutting down timeseries collection and aggregation: {e}")

    # Shutdown monitoring
    shutdown_monitoring()

app = FastAPI(
    title="AccountDB API",
    description="""
    # AccountDB API

    API for managing Steam accounts, hardware profiles, cards, and user authentication.

    ## Features

    * **Authentication**: JWT-based authentication with role-based access control
    * **Account Management**: Create, read, update, and delete Steam accounts
    * **Hardware Management**: Manage hardware profiles associated with accounts
    * **Card Management**: Manage Steam gift cards
    * **Steam Authentication**: Generate Steam Guard 2FA codes and manage Steam authentication
    * **Account Status**: Manage account status (lock, prime, etc.)
    * **Bulk Operations**: Support for bulk account creation and status updates

    ## Authentication

    Most endpoints require authentication using a JWT token. To authenticate:

    1. Get a token using the `/auth/token` endpoint
    2. Include the token in the `Authorization` header as `Bearer {token}`

    ## Row-Level Security (RLS)

    The API uses PostgreSQL Row-Level Security (RLS) to ensure that users can only access their own data.
    Administrators can access all data.
    """,
    version="1.0.0",
    lifespan=lifespan,
    contact={
        "name": "AccountDB Support",
        "email": "support@accountdb.example.com",
    },
    license_info={
        "name": "Proprietary",
        "url": "https://accountdb.example.com/license",
    },
    openapi_tags=[
        {
            "name": "auth",
            "description": "Authentication and user management operations",
        },
        {
            "name": "accounts",
            "description": "Steam account management operations",
        },
        {
            "name": "hardware",
            "description": "Hardware profile management operations",
        },
        {
            "name": "cards",
            "description": "Steam gift card management operations",
        },
        {
            "name": "steam-auth",
            "description": "Steam authentication operations",
        },
        {
            "name": "account-status",
            "description": "Account status management operations",
        },
        {
            "name": "upload",
            "description": "File upload operations for bulk account creation",
        },
        {
            "name": "vms",
            "description": "Virtual machine management operations",
        },
        {
            "name": "vm-access",
            "description": "Virtual machine access control operations",
        },
        {
            "name": "timeseries",
            "description": "Timeseries data for performance metrics and statistics",
        },
        {
            "name": "ban-check",
            "description": "Steam profile ban checker with proxy and retry support",
        },
    ],
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Configure CORS
logger.info(f"CORS allowed origins: {Config.CORS_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    window=60,  # 1 minute
    max_requests=100,  # 100 requests per minute
    exclude_paths=["/health", "/api/docs", "/api/redoc", "/openapi.json"]
)

# Add timeout middleware
app.add_middleware(
    TimeoutMiddleware,
    timeout=30,  # 30 seconds
    exclude_paths=["/upload", "/accounts/list/stream"]
)

# Add size limit middleware
app.add_middleware(
    SizeLimitMiddleware,
    max_size=10 * 1024 * 1024,  # 10 MB
    exclude_paths=["/upload"]
)

# Add tracing middleware
app.add_middleware(
    TracingMiddleware
)

# Set up error handling
setup_error_handling(app)

# Add middleware for request ID and timing
@app.middleware("http")
async def add_request_id_and_timing(request: Request, call_next):
    # Add request ID
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = f"req_{int(time.time() * 1000)}"

    # Add start time
    start_time = time.time()

    # Record active request
    from monitoring import record_active_request
    method = request.method
    endpoint = request.url.path
    record_active_request(method, endpoint, True)

    try:
        # Process the request
        response = await call_next(request)

        # Calculate processing time
        processing_time = time.time() - start_time

        # Add headers to the response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Processing-Time"] = str(processing_time)

        # Record request
        from monitoring import record_request
        record_request(method, endpoint, response.status_code, processing_time)

        return response
    except Exception as e:
        # Record error
        from monitoring import record_error
        record_error(method, endpoint, type(e).__name__)

        # Re-raise the exception
        raise
    finally:
        # Record inactive request
        record_active_request(method, endpoint, False)

# Include routers
app.include_router(auth.router)  # Auth router should be first for proper dependency resolution
app.include_router(accounts.router)
app.include_router(cards.router)
app.include_router(hardware.router)
app.include_router(steam_auth.router)
app.include_router(account_status.router)
app.include_router(upload.router)
app.include_router(vms.router)
app.include_router(proxmox_nodes.router)
app.include_router(vm_access.router)
app.include_router(monitoring.router)
app.include_router(windows_vm_agent.router)
app.include_router(settings.router)
app.include_router(timeseries.router)
app.include_router(farmlabs.router)
app.include_router(logs.router)
app.include_router(ban_check.router)
app.include_router(downloads.router)

@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    from monitoring import check_health, get_health_status

    # Check health
    check_health()

    # Get health status
    health_status = get_health_status()

    return health_status

@app.get("/error-test")
async def error_test():
    """Test endpoint for error handling."""
    # This will be caught by our error handling system
    raise ValueError("This is a test error")

@app.get("/error-summary")
async def error_summary():
    """Get a summary of tracked errors."""
    from error_handling.reporting import get_error_summary
    return get_error_summary()

@app.get("/monitoring")
async def monitoring_status():
    """Get monitoring status."""
    from monitoring import get_monitoring_config
    from monitoring.metrics import REQUEST_COUNT, REQUEST_LATENCY, ACTIVE_REQUESTS, ERROR_COUNT
    from monitoring.health import get_health_status
    from monitoring.alerting import get_alert_status

    # Get monitoring configuration
    monitoring_config = get_monitoring_config()

    # Get health status
    health_status = get_health_status()

    # Get alert status
    alert_status = get_alert_status()

    # Get metrics
    metrics = {
        "request_count": {
            "total": sum([REQUEST_COUNT._value.get() for REQUEST_COUNT in REQUEST_COUNT._metrics.values()])
        },
        "active_requests": {
            "total": sum([ACTIVE_REQUESTS._value.get() for ACTIVE_REQUESTS in ACTIVE_REQUESTS._metrics.values()])
        },
        "error_count": {
            "total": sum([ERROR_COUNT._value.get() for ERROR_COUNT in ERROR_COUNT._metrics.values()])
        }
    }

    return {
        "config": monitoring_config,
        "health": health_status,
        "alerts": alert_status,
        "metrics": metrics
    }
