"""
FarmLabs API router.

This module provides endpoints for FarmLabs integration, including webhooks for job completion.
It handles Discord webhook integration for FarmLabs bot job notifications.
"""

import logging
import re
import json
from typing import Dict, Any, Optional, List, Union
from fastapi import APIRouter, Depends, HTTPException, Query, Body, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from datetime import datetime

from db.repositories.farmlabs import FarmLabsRepository
from routers.auth import get_current_user

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/farmlabs",
    tags=["farmlabs"],
    responses={404: {"description": "Not found"}},
)

# Models
class DiscordEmbed(BaseModel):
    """Model for Discord embed objects."""
    title: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    color: Optional[int] = None
    fields: Optional[List[Dict[str, Any]]] = None

class DiscordWebhook(BaseModel):
    """Model for Discord webhook payload."""
    content: Optional[str] = None
    embeds: Optional[List[Dict[str, Any]]] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None

    @validator('embeds', pre=True, always=True)
    def validate_embeds(cls, v, values):
        """Process embeds and ensure they're properly formatted."""
        # If embeds is None but content is provided, that's fine
        if v is None and values.get('content'):
            return v

        # If both content and embeds are None, that's an error
        if v is None and not values.get('content'):
            raise ValueError("Either content or embeds must be provided")

        # Return the embeds as is
        return v

class JobCompletionWebhook(BaseModel):
    """Model for job completion webhook."""
    job_id: str = Field(..., description="Unique identifier for the job")
    vm_id: Optional[str] = Field(None, description="ID of the VM that ran the job")
    bot_account_id: Optional[str] = Field(None, description="ID of the bot account that ran the job")
    status: str = Field(..., description="Status of the job (completed, failed, etc.)")
    job_type: str = Field(..., description="Type of job that was run")
    start_time: Optional[str] = Field(None, description="ISO timestamp when the job started")
    end_time: str = Field(..., description="ISO timestamp when the job completed")
    result_data: Dict[str, Any] = Field(default_factory=dict, description="Result data from the job")

class WebhookResponse(BaseModel):
    """Response model for webhooks."""
    success: bool = Field(..., description="Whether the webhook was processed successfully")
    message: str = Field(..., description="Message describing the result")
    job_id: Optional[str] = Field(None, description="ID of the job that was processed")

# Helper functions
def parse_discord_webhook(discord_data: DiscordWebhook) -> Optional[JobCompletionWebhook]:
    """
    Parse a Discord webhook payload into a JobCompletionWebhook object.

    Args:
        discord_data: The Discord webhook payload

    Returns:
        A JobCompletionWebhook object or None if parsing fails
    """
    try:
        # Initialize with default values
        job_data = {
            "job_id": "",
            "vm_id": None,
            "bot_account_id": None,
            "status": "completed",
            "job_type": "unknown",
            "start_time": None,
            "end_time": datetime.now().isoformat(),
            "result_data": {}
        }

        # Extract data from Discord content
        content = discord_data.content or ""

        # Try to extract job ID using regex patterns
        job_id_match = re.search(r'Job ID[:\s]+([a-zA-Z0-9-_]+)', content, re.IGNORECASE)
        if job_id_match:
            job_data["job_id"] = job_id_match.group(1)

        # Extract VM ID if present
        vm_id_match = re.search(r'VM ID[:\s]+([a-zA-Z0-9-_]+)', content, re.IGNORECASE)
        if vm_id_match:
            job_data["vm_id"] = vm_id_match.group(1)

        # Extract bot account ID if present
        bot_id_match = re.search(r'Bot ID[:\s]+([a-zA-Z0-9-_]+)', content, re.IGNORECASE)
        if bot_id_match:
            job_data["bot_account_id"] = bot_id_match.group(1)

        # Extract job type if present
        job_type_match = re.search(r'Job Type[:\s]+([a-zA-Z0-9-_\s]+)', content, re.IGNORECASE)
        if job_type_match:
            job_data["job_type"] = job_type_match.group(1).strip()

        # Extract status if present
        status_match = re.search(r'Status[:\s]+([a-zA-Z0-9-_\s]+)', content, re.IGNORECASE)
        if status_match:
            job_data["status"] = status_match.group(1).strip().lower()

        # If there are embeds, try to extract more structured data
        if discord_data.embeds:
            for embed in discord_data.embeds:
                # Check if this is a test notification
                if isinstance(embed, dict) and embed.get("title") == "Test Notification":
                    job_data["job_id"] = f"test-{int(datetime.now().timestamp())}"
                    job_data["job_type"] = "test_notification"
                    job_data["status"] = "completed"
                    job_data["result_data"] = {
                        "description": embed.get("description", "Test notification"),
                        "source": "discord_webhook"
                    }
                    continue

                # Extract data from embed description if available
                if isinstance(embed, dict) and embed.get("description"):
                    description = embed.get("description", "")

                    # Try to extract data from the description
                    job_id_match = re.search(r'Job ID[:\s]+([a-zA-Z0-9-_]+)', description, re.IGNORECASE)
                    if job_id_match:
                        job_data["job_id"] = job_id_match.group(1)

                    vm_id_match = re.search(r'VM ID[:\s]+([a-zA-Z0-9-_]+)', description, re.IGNORECASE)
                    if vm_id_match:
                        job_data["vm_id"] = vm_id_match.group(1)

                    bot_id_match = re.search(r'Bot ID[:\s]+([a-zA-Z0-9-_]+)', description, re.IGNORECASE)
                    if bot_id_match:
                        job_data["bot_account_id"] = bot_id_match.group(1)

                # Extract data from embed fields if available
                fields = embed.get("fields") if isinstance(embed, dict) else getattr(embed, "fields", None)
                if fields:
                    for field in fields:
                        field_name = field.get("name", "").lower()
                        field_value = field.get("value", "")

                        if "job id" in field_name:
                            job_data["job_id"] = field_value.strip()
                        elif "vm id" in field_name:
                            job_data["vm_id"] = field_value.strip()
                        elif "bot id" in field_name or "account id" in field_name:
                            job_data["bot_account_id"] = field_value.strip()
                        elif "status" in field_name:
                            job_data["status"] = field_value.strip().lower()
                        elif "job type" in field_name or "type" in field_name:
                            job_data["job_type"] = field_value.strip()
                        elif "start time" in field_name:
                            job_data["start_time"] = field_value.strip()
                        elif "end time" in field_name or "completion time" in field_name:
                            job_data["end_time"] = field_value.strip()
                        elif "result" in field_name or "data" in field_name:
                            try:
                                job_data["result_data"] = json.loads(field_value)
                            except:
                                job_data["result_data"] = {"raw_data": field_value}

        # Generate a job ID if none was found
        if not job_data["job_id"]:
            job_data["job_id"] = f"discord-{int(datetime.now().timestamp())}"

        # Create and return the JobCompletionWebhook object
        return JobCompletionWebhook(**job_data)

    except Exception as e:
        logger.error(f"Error parsing Discord webhook: {e}")
        return None

# Endpoints
@router.post("/webhook/job-completion", response_model=WebhookResponse)
async def job_completion_webhook(
    request: Request,
    api_key: str = Query(..., description="API key for authentication"),
):
    """
    Webhook endpoint for FarmLabs job completion.

    This endpoint is called by Discord when a FarmLabs bot job is completed.
    It requires an API key for authentication.
    """
    try:
        # Get the raw request body
        body = await request.json()
        logger.info(f"Received Discord webhook: {body}")

        try:
            # Parse the Discord webhook
            discord_data = DiscordWebhook(**body)
            webhook_data = parse_discord_webhook(discord_data)
        except Exception as e:
            logger.error(f"Error parsing Discord webhook format: {e}")
            # Try to create a simple test notification if parsing fails
            webhook_data = JobCompletionWebhook(
                job_id=f"test-{int(datetime.now().timestamp())}",
                status="completed",
                job_type="test_notification",
                end_time=datetime.now().isoformat(),
                result_data={"raw_data": body, "error": str(e)}
            )

        if not webhook_data:
            logger.error("Failed to parse Discord webhook")
            return WebhookResponse(
                success=False,
                message="Failed to parse Discord webhook",
                job_id=None
            )

        logger.info(f"Parsed webhook data: job_id={webhook_data.job_id}, vm_id={webhook_data.vm_id}, bot_account_id={webhook_data.bot_account_id}")

        # Initialize repository with admin context for API key validation
        farmlabs_repo = FarmLabsRepository(user_id=1, user_role="admin")

        # Verify API key
        if not farmlabs_repo.verify_api_key(api_key, webhook_data.vm_id):
            logger.warning(f"Invalid API key for job completion webhook: {api_key[:5]}...")
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Record the job completion
        job_data = webhook_data.dict()
        result = farmlabs_repo.record_job_completion(job_data)

        if not result:
            logger.error(f"Failed to record job completion for job_id={webhook_data.job_id}")
            return WebhookResponse(
                success=False,
                message="Failed to record job completion",
                job_id=webhook_data.job_id
            )

        logger.info(f"Successfully recorded job completion for job_id={webhook_data.job_id}")
        return WebhookResponse(
            success=True,
            message="Job completion recorded successfully",
            job_id=webhook_data.job_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing job completion webhook: {e}")
        return WebhookResponse(
            success=False,
            message=f"Error processing webhook: {str(e)}",
            job_id=None
        )

