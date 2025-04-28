"""
Main application for the Proxmox host agent.
"""

import asyncio
import time
import signal
import sys
from typing import Dict, Any, List
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from loguru import logger
import uvicorn

from config import config
from proxmox_client import ProxmoxClient
from accountdb_client import AccountDBClient

# Configure logger
logger.remove()
logger.add(
    sys.stdout,
    level="DEBUG",  # Force DEBUG level for more verbose logging
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)

# Create FastAPI app
app = FastAPI(
    title="Proxmox Host Agent",
    description="Agent for synchronizing Proxmox VM information with AccountDB",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create clients
proxmox_client = ProxmoxClient()
accountdb_client = AccountDBClient()

# Global variables
sync_task = None
last_sync_time = 0
last_sync_stats = {}
last_whitelist_update_time = 0
whitelist_cache = []
is_running = True

class SyncResponse(BaseModel):
    """Response model for synchronization status."""
    last_sync_time: int
    last_sync_stats: Dict[str, int] = Field(default_factory=dict)
    is_syncing: bool
    update_interval: int
    whitelist: List[int] = Field(default_factory=list)
    whitelist_enabled: bool
    whitelist_last_updated: int = Field(default_factory=lambda: int(time.time()))

    model_config = {
        "arbitrary_types_allowed": True
    }

async def verify_connection():
    """Verify the connection to the AccountDB API."""
    try:
        logger.info("Verifying connection to AccountDB")
        success = await accountdb_client.verify_connection()
        if success:
            logger.info("Connection to AccountDB verified successfully")
        else:
            logger.error("Failed to verify connection to AccountDB")
        return success
    except Exception as e:
        logger.error(f"Error verifying connection to AccountDB: {e}")
        return False

async def send_heartbeat():
    """Send a heartbeat to the AccountDB API."""
    try:
        logger.debug("Sending heartbeat to AccountDB")
        success = await accountdb_client.send_heartbeat()
        if not success:
            logger.warning("Failed to send heartbeat to AccountDB")
        return success
    except Exception as e:
        logger.error(f"Error sending heartbeat to AccountDB: {e}")
        return False

async def sync_vms():
    """Synchronize VMs between Proxmox and AccountDB."""
    global last_sync_time, last_sync_stats, last_whitelist_update_time, whitelist_cache

    try:
        logger.info("Starting VM synchronization")

        # Verify connection first
        if not await verify_connection():
            logger.error("Cannot synchronize VMs: Connection to AccountDB not verified")
            return

        # Get the latest whitelist
        try:
            whitelist = await accountdb_client.get_vmid_whitelist()
            whitelist_enabled = len(whitelist) > 0

            # Update whitelist cache and timestamp
            whitelist_cache = whitelist
            last_whitelist_update_time = int(time.time())

            logger.info(f"Retrieved whitelist with {len(whitelist)} VMIDs. Whitelist enabled: {whitelist_enabled}")
        except Exception as e:
            # If we can't get the whitelist, use the cached version if available
            if len(whitelist_cache) > 0:
                logger.warning(f"Error retrieving whitelist, using cached version: {e}")
                whitelist = whitelist_cache
                whitelist_enabled = len(whitelist) > 0
            else:
                # If no cache is available, proceed without filtering
                logger.error(f"Error retrieving whitelist and no cache available: {e}")
                whitelist = []
                whitelist_enabled = False

        # Get VMs from Proxmox
        vms = proxmox_client.get_vms()
        logger.info(f"Retrieved {len(vms)} VMs from Proxmox")

        # Filter VMs based on whitelist if enabled
        original_vm_count = len(vms)
        if whitelist_enabled:
            filtered_vms = [vm for vm in vms if vm.get('vmid') in whitelist]
            logger.info(f"Filtered VMs based on whitelist: {len(filtered_vms)} of {original_vm_count} VMs will be synced")
            vms = filtered_vms

        # Sync with AccountDB
        stats = await accountdb_client.sync_vms(vms)

        # Add additional stats
        stats["total_vms_before_filter"] = original_vm_count
        stats["total_vms_after_filter"] = len(vms)
        stats["filtered_out"] = original_vm_count - len(vms)
        stats["whitelist_count"] = len(whitelist)
        stats["whitelist_enabled"] = whitelist_enabled
        stats["whitelist_last_updated"] = last_whitelist_update_time
        stats["used_cached_whitelist"] = whitelist is whitelist_cache and len(whitelist_cache) > 0

        # Update sync status
        last_sync_time = int(time.time())
        last_sync_stats = stats

        logger.info(f"VM synchronization completed: {stats}")
    except Exception as e:
        logger.error(f"Error during VM synchronization: {e}")

async def scheduled_sync():
    """Run VM synchronization and heartbeat on a schedule."""
    global is_running

    # Verify connection on startup
    await verify_connection()

    # Initial sync
    await sync_vms()

    heartbeat_interval = min(60, config.update_interval)  # Send heartbeat at most every minute
    last_heartbeat = time.time()

    while is_running:
        current_time = time.time()

        # Send heartbeat if needed
        if current_time - last_heartbeat >= heartbeat_interval:
            await send_heartbeat()
            last_heartbeat = current_time

        # Run sync if needed
        if current_time - last_sync_time >= config.update_interval:
            await sync_vms()

        # Sleep for a short time to avoid busy waiting
        await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    """Run when the application starts."""
    global sync_task

    logger.info("Starting Proxmox Host Agent")

    # Start scheduled sync task
    sync_task = asyncio.create_task(scheduled_sync())

    logger.info(f"Scheduled sync task started (interval: {config.update_interval} seconds)")

@app.on_event("shutdown")
async def shutdown_event():
    """Run when the application shuts down."""
    global is_running, sync_task

    logger.info("Shutting down Proxmox Host Agent")

    # Stop scheduled sync task
    is_running = False
    if sync_task:
        sync_task.cancel()
        try:
            await sync_task
        except asyncio.CancelledError:
            pass

    logger.info("Scheduled sync task stopped")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "timestamp": int(time.time())}

@app.get("/sync/status", response_model=SyncResponse)
async def sync_status():
    """Get synchronization status."""
    global whitelist_cache, last_whitelist_update_time

    # Check if we need to refresh the whitelist (if it's empty or older than 5 minutes)
    current_time = int(time.time())
    whitelist_age = current_time - last_whitelist_update_time
    need_refresh = len(whitelist_cache) == 0 or whitelist_age > 300  # 5 minutes

    if need_refresh:
        logger.info(f"Refreshing whitelist (age: {whitelist_age} seconds)")
        # Get fresh whitelist
        whitelist = await accountdb_client.get_vmid_whitelist()
        whitelist_cache = whitelist
        last_whitelist_update_time = current_time
    else:
        # Use cached whitelist
        whitelist = whitelist_cache
        logger.debug(f"Using cached whitelist (age: {whitelist_age} seconds)")

    whitelist_enabled = len(whitelist) > 0

    # Update last_sync_stats with whitelist info if it exists
    if isinstance(last_sync_stats, dict):
        last_sync_stats_copy = last_sync_stats.copy()
        last_sync_stats_copy["whitelist_count"] = len(whitelist)
        last_sync_stats_copy["whitelist_enabled"] = whitelist_enabled
        last_sync_stats_copy["whitelist_age_seconds"] = whitelist_age
    else:
        last_sync_stats_copy = {
            "whitelist_count": len(whitelist),
            "whitelist_enabled": whitelist_enabled,
            "whitelist_age_seconds": whitelist_age
        }

    return {
        "last_sync_time": last_sync_time,
        "last_sync_stats": last_sync_stats_copy,
        "is_syncing": sync_task is not None and not sync_task.done(),
        "update_interval": config.update_interval,
        "whitelist": whitelist,
        "whitelist_enabled": whitelist_enabled,
        "whitelist_last_updated": last_whitelist_update_time,
    }

@app.post("/sync/trigger")
async def trigger_sync(background_tasks: BackgroundTasks):
    """Trigger a manual synchronization."""
    background_tasks.add_task(sync_vms)
    return {"status": "sync_triggered", "timestamp": int(time.time())}

@app.post("/whitelist/refresh")
async def refresh_whitelist():
    """Force refresh the whitelist cache."""
    global whitelist_cache, last_whitelist_update_time

    try:
        # Get fresh whitelist
        whitelist = await accountdb_client.get_vmid_whitelist()
        whitelist_cache = whitelist
        last_whitelist_update_time = int(time.time())

        return {
            "status": "whitelist_refreshed",
            "timestamp": last_whitelist_update_time,
            "whitelist_count": len(whitelist),
            "whitelist_enabled": len(whitelist) > 0
        }
    except Exception as e:
        logger.error(f"Error refreshing whitelist: {e}")
        raise HTTPException(status_code=500, detail=f"Error refreshing whitelist: {str(e)}")

@app.get("/vms")
async def get_vms():
    """Get all VMs from Proxmox."""
    vms = proxmox_client.get_vms()
    return {"vms": vms, "count": len(vms)}

@app.get("/vms/{vm_id}")
async def get_vm(vm_id: int):
    """Get a specific VM from Proxmox."""
    vms = proxmox_client.get_vms()
    for vm in vms:
        if vm.get("vmid") == vm_id:
            return vm
    raise HTTPException(status_code=404, detail="VM not found")

@app.get("/config")
async def get_config():
    """Get application configuration (excluding sensitive information)."""
    return {
        "proxmox": {
            "host": config.proxmox.host,
            "user": config.proxmox.user,
            "verify_ssl": config.proxmox.verify_ssl,
            "node_name": config.proxmox.node_name,
        },
        "accountdb": {
            "url": config.accountdb.url,
            "owner_id": config.accountdb.owner_id,
        },
        "update_interval": config.update_interval,
        "log_level": config.log_level,
        "debug": config.debug,
    }

def handle_sigterm(signum, frame):
    """Handle SIGTERM signal."""
    logger.info("Received SIGTERM signal")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGTERM, handle_sigterm)

    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.debug,
    )
