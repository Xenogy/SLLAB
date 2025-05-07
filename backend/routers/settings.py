"""
Settings API endpoints.

This module provides API endpoints for managing user settings and API keys.
"""
import logging
import secrets
import string
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from pydantic import BaseModel, Field

from db.repositories.settings import SettingsRepository
from db import get_user_db_connection
from routers.auth import get_current_user, get_current_active_user

# Configure logging
logger = logging.getLogger(__name__)

# Router
router = APIRouter(
    prefix="/settings",
    tags=["settings"],
    responses={404: {"description": "Not found"}},
)

# Models
class UserSettingsBase(BaseModel):
    theme: Optional[str] = Field(None, description="UI theme (light, dark, system)")
    language: Optional[str] = Field(None, description="UI language")
    timezone: Optional[str] = Field(None, description="User's timezone")
    date_format: Optional[str] = Field(None, description="Date format preference")
    time_format: Optional[str] = Field(None, description="Time format preference (12h, 24h)")
    notifications_enabled: Optional[bool] = Field(None, description="Whether notifications are enabled")
    email_notifications: Optional[bool] = Field(None, description="Whether email notifications are enabled")
    auto_refresh_interval: Optional[int] = Field(None, description="Auto-refresh interval in seconds")
    items_per_page: Optional[int] = Field(None, description="Number of items per page in lists")

class UserSettingsResponse(UserSettingsBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

class APIKeyBase(BaseModel):
    key_name: str = Field(..., description="Name/description of the API key")
    key_type: Optional[str] = Field("user", description="Type of API key (user, proxmox_node, windows_vm, farmlabs)")
    expires_in_days: Optional[int] = Field(None, description="Number of days until the key expires (null = never expires)")
    scopes: Optional[List[str]] = Field(None, description="Permission scopes for the API key")

class APIKeyResponse(BaseModel):
    id: int
    user_id: int
    key_name: str
    api_key_prefix: str
    scopes: List[str]
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    created_at: datetime
    revoked: bool
    key_type: str = Field("user", description="Type of API key (user, proxmox_node, windows_vm, farmlabs)")
    resource_id: Optional[int] = Field(None, description="ID of the associated resource (proxmox node ID or VM ID)")

class APIKeyCreateResponse(APIKeyResponse):
    api_key: str = Field(..., description="The full API key (only shown once)")

class APIKeyListResponse(BaseModel):
    api_keys: List[APIKeyResponse]
    total: int

class ResourceAPIKeyRequest(BaseModel):
    resource_type: str = Field(..., description="Type of resource (proxmox_node, windows_vm)")
    resource_id: int = Field(..., description="ID of the resource")

class ResourceAPIKeyResponse(APIKeyCreateResponse):
    pass

# Endpoints for User Settings
@router.get("/user", response_model=UserSettingsResponse)
async def get_user_settings(current_user: dict = Depends(get_current_active_user)):
    """
    Get the current user's settings.
    """
    logger.info(f"Getting settings for user ID: {current_user['id']}")

    try:
        # Initialize the settings repository with the current user's context
        settings_repo = SettingsRepository(user_id=current_user["id"], user_role=current_user["role"])

        # Get the user's settings
        settings = settings_repo.get_user_settings(current_user["id"])

        if not settings:
            # Create default settings if none exist
            settings = settings_repo.create_user_settings(current_user["id"])

        return settings

    except Exception as e:
        logger.error(f"Error getting user settings: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting user settings: {str(e)}")

@router.patch("/user", response_model=UserSettingsResponse)
async def update_user_settings(
    settings: UserSettingsBase,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Update the current user's settings.
    """
    logger.info(f"Updating settings for user ID: {current_user['id']}")

    try:
        # Initialize the settings repository with the current user's context
        settings_repo = SettingsRepository(user_id=current_user["id"], user_role=current_user["role"])

        # Update the user's settings
        updated_settings = settings_repo.update_user_settings(current_user["id"], settings.dict(exclude_unset=True))

        return updated_settings

    except Exception as e:
        logger.error(f"Error updating user settings: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating user settings: {str(e)}")

# Endpoints for API Keys
@router.get("/api-keys", response_model=APIKeyListResponse)
async def list_api_keys(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    include_revoked: bool = Query(False),
    current_user: dict = Depends(get_current_active_user)
):
    """
    List the current user's API keys.
    """
    logger.info(f"Listing API keys for user ID: {current_user['id']}")

    try:
        # Initialize the settings repository with the current user's context
        settings_repo = SettingsRepository(user_id=current_user["id"], user_role=current_user["role"])

        # Get the user's API keys
        api_keys, total = settings_repo.list_api_keys(
            user_id=current_user["id"],
            limit=limit,
            offset=offset,
            include_revoked=include_revoked
        )

        return {"api_keys": api_keys, "total": total}

    except Exception as e:
        logger.error(f"Error listing API keys: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing API keys: {str(e)}")

@router.post("/api-keys", response_model=APIKeyCreateResponse)
async def create_api_key(
    api_key: APIKeyBase,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Create a new API key for the current user.
    """
    logger.info(f"Creating API key for user ID: {current_user['id']}")

    try:
        # Initialize the settings repository with the current user's context
        settings_repo = SettingsRepository(user_id=current_user["id"], user_role=current_user["role"])

        # Generate a random API key
        api_key_value = generate_api_key()

        # Calculate expiration date if provided
        expires_at = None
        if api_key.expires_in_days is not None:
            expires_at = datetime.now() + timedelta(days=api_key.expires_in_days)

        # Create the API key
        new_api_key = settings_repo.create_api_key(
            user_id=current_user["id"],
            key_name=api_key.key_name,
            api_key=api_key_value,
            scopes=api_key.scopes or [],
            expires_at=expires_at,
            key_type=api_key.key_type or "user"
        )

        # Add the full API key to the response (only shown once)
        new_api_key["api_key"] = api_key_value

        return new_api_key

    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating API key: {str(e)}")

@router.delete("/api-keys/{key_id}", response_model=APIKeyResponse)
async def revoke_api_key(
    key_id: int = Path(..., description="The ID of the API key to revoke"),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Revoke an API key.
    """
    logger.info(f"Revoking API key ID {key_id} for user ID: {current_user['id']}")

    try:
        # Initialize the settings repository with the current user's context
        settings_repo = SettingsRepository(user_id=current_user["id"], user_role=current_user["role"])

        # Check if the API key exists and belongs to the user
        api_key = settings_repo.get_api_key(key_id)
        if not api_key:
            raise HTTPException(status_code=404, detail="API key not found")

        if api_key["user_id"] != current_user["id"] and current_user["role"] != "admin":
            raise HTTPException(status_code=403, detail="You don't have permission to revoke this API key")

        # Revoke the API key
        revoked_api_key = settings_repo.revoke_api_key(key_id)

        return revoked_api_key

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking API key: {e}")
        raise HTTPException(status_code=500, detail=f"Error revoking API key: {str(e)}")

# Endpoints for Resource API Keys
@router.get("/resource-api-keys", response_model=APIKeyListResponse)
async def list_resource_api_keys(
    resource_type: str = Query(..., description="Type of resource (proxmox_node, windows_vm)"),
    resource_id: int = Query(..., description="ID of the resource"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    include_revoked: bool = Query(False),
    current_user: dict = Depends(get_current_active_user)
):
    """
    List API keys for a specific resource.
    """
    logger.info(f"Listing API keys for resource type {resource_type}, ID {resource_id}")

    try:
        # Initialize the settings repository with the current user's context
        settings_repo = SettingsRepository(user_id=current_user["id"], user_role=current_user["role"])

        # Validate resource type
        if resource_type not in ["proxmox_node", "windows_vm", "farmlabs"]:
            raise HTTPException(status_code=400, detail="Invalid resource type")

        # Check if the user has access to the resource
        if current_user["role"] != "admin":
            # For Proxmox nodes
            if resource_type == "proxmox_node":
                # Check if the node exists and belongs to the user
                with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            "SELECT owner_id FROM proxmox_nodes WHERE id = %s",
                            (resource_id,)
                        )
                        result = cursor.fetchone()
                        if not result or result[0] != current_user["id"]:
                            raise HTTPException(status_code=403, detail="You don't have permission to access this resource")

            # For Windows VMs
            elif resource_type == "windows_vm":
                # Check if the VM exists and belongs to the user
                with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            "SELECT owner_id FROM vms WHERE id = %s",
                            (resource_id,)
                        )
                        result = cursor.fetchone()
                        if not result or result[0] != current_user["id"]:
                            raise HTTPException(status_code=403, detail="You don't have permission to access this resource")

            # For FarmLabs API keys, no resource ID is needed
            elif resource_type == "farmlabs":
                # No specific resource check needed for FarmLabs
                pass

        # Get the resource API keys
        api_keys, total = settings_repo.list_api_keys(
            user_id=current_user["id"],
            limit=limit,
            offset=offset,
            include_revoked=include_revoked,
            key_type=resource_type,
            resource_id=resource_id
        )

        return {"api_keys": api_keys, "total": total}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing resource API keys: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing resource API keys: {str(e)}")

@router.post("/resource-api-keys", response_model=ResourceAPIKeyResponse)
async def create_resource_api_key(
    request: ResourceAPIKeyRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Create a new API key for a resource.
    """
    logger.info(f"Creating API key for resource type {request.resource_type}, ID {request.resource_id}")

    try:
        # Initialize the settings repository with the current user's context
        settings_repo = SettingsRepository(user_id=current_user["id"], user_role=current_user["role"])

        # Validate resource type
        if request.resource_type not in ["proxmox_node", "windows_vm", "farmlabs"]:
            raise HTTPException(status_code=400, detail="Invalid resource type")

        # Check if the user has access to the resource
        if current_user["role"] != "admin":
            # For Proxmox nodes
            if request.resource_type == "proxmox_node":
                # Check if the node exists and belongs to the user
                with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            "SELECT owner_id FROM proxmox_nodes WHERE id = %s",
                            (request.resource_id,)
                        )
                        result = cursor.fetchone()
                        if not result or result[0] != current_user["id"]:
                            raise HTTPException(status_code=403, detail="You don't have permission to access this resource")

            # For Windows VMs
            elif request.resource_type == "windows_vm":
                # Check if the VM exists and belongs to the user
                with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute(
                            "SELECT owner_id FROM vms WHERE id = %s",
                            (request.resource_id,)
                        )
                        result = cursor.fetchone()
                        if not result or result[0] != current_user["id"]:
                            raise HTTPException(status_code=403, detail="You don't have permission to access this resource")

            # For FarmLabs API keys, no resource ID is needed
            elif request.resource_type == "farmlabs":
                # No specific resource check needed for FarmLabs
                pass

        # Generate a random API key
        api_key_value = generate_api_key()

        # Regenerate the API key for the resource
        new_api_key = settings_repo.regenerate_api_key_for_resource(
            key_type=request.resource_type,
            resource_id=request.resource_id,
            api_key=api_key_value
        )

        if not new_api_key:
            raise HTTPException(status_code=500, detail="Failed to create API key for resource")

        # Add the full API key to the response (only shown once)
        new_api_key["api_key"] = api_key_value

        return new_api_key

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating resource API key: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating resource API key: {str(e)}")

# Helper functions
def generate_api_key(length: int = 32) -> str:
    """
    Generate a random API key.

    Args:
        length: Length of the API key (default: 32)

    Returns:
        A random API key string
    """
    alphabet = string.ascii_letters + string.digits
    api_key = ''.join(secrets.choice(alphabet) for _ in range(length))
    return api_key
