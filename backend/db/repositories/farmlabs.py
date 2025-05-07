"""
FarmLabs repository for the AccountDB API.

This module provides database access methods for FarmLabs data.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from .base import BaseRepository
from ..repositories.settings import SettingsRepository

# Configure logging
logger = logging.getLogger(__name__)

class FarmLabsRepository(BaseRepository):
    """Repository for FarmLabs data."""

    def __init__(self, user_id: Optional[int] = None, user_role: Optional[str] = None):
        """
        Initialize the FarmLabsRepository instance.

        Args:
            user_id (Optional[int], optional): The ID of the user for RLS context. Defaults to None.
            user_role (Optional[str], optional): The role of the user for RLS context. Defaults to None.
        """
        super().__init__(user_id, user_role)
        self.table_name = "farmlabs_jobs"
        self.id_column = "id"
        self.default_columns = """
            id, job_id, vm_id, bot_account_id, status, job_type, start_time,
            end_time, result_data, created_at, updated_at, owner_id
        """
        self.default_order_by = "id DESC"
        self.search_columns = ["job_id", "vm_id", "status", "job_type"]

    def record_job_completion(self, job_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Record a completed job from FarmLabs.

        Args:
            job_data (Dict[str, Any]): The job completion data.

        Returns:
            Optional[Dict[str, Any]]: The recorded job data or None if failed.
        """
        try:
            # Extract data from the webhook payload
            job_id = job_data.get("job_id")
            vm_id = job_data.get("vm_id")
            bot_account_id = job_data.get("bot_account_id")
            status = job_data.get("status", "completed")
            job_type = job_data.get("job_type", "unknown")
            start_time = job_data.get("start_time")
            end_time = job_data.get("end_time", datetime.now().isoformat())

            # Store result data as JSON
            result_data = json.dumps(job_data.get("result_data", {}))

            # Get owner_id from VM if available
            owner_id = self.get_vm_owner_id(vm_id) if vm_id else self.user_id

            # Prepare data for insertion
            insert_data = {
                "job_id": job_id,
                "vm_id": vm_id,
                "bot_account_id": bot_account_id,
                "status": status,
                "job_type": job_type,
                "start_time": start_time,
                "end_time": end_time,
                "result_data": result_data,
                "owner_id": owner_id
            }

            # Insert the job record
            return self.create(insert_data)

        except Exception as e:
            logger.error(f"Error recording job completion: {e}")
            return None

    def get_vm_owner_id(self, vm_id: str) -> Optional[int]:
        """
        Get the owner ID of a VM.

        Args:
            vm_id (str): The VM ID.

        Returns:
            Optional[int]: The owner ID or None if not found.
        """
        try:
            query = """
                SELECT owner_id FROM vms WHERE vmid = %s
            """
            result = self.execute_query_single(query, (vm_id,))
            return result["owner_id"] if result else self.user_id
        except Exception as e:
            logger.error(f"Error getting VM owner ID: {e}")
            return self.user_id

    def verify_api_key(self, api_key: str, vm_id: Optional[str] = None) -> bool:
        """
        Verify an API key for FarmLabs webhook.

        Args:
            api_key (str): The API key to verify.
            vm_id (Optional[str]): The VM ID associated with the request.

        Returns:
            bool: True if the API key is valid, False otherwise.
        """
        try:
            # Use the settings repository to validate the API key
            settings_repo = SettingsRepository(user_id=1, user_role="admin")  # Use admin role for verification

            # Validate the API key
            api_key_data = settings_repo.validate_api_key(
                api_key=api_key,
                key_type="farmlabs"
            )

            return api_key_data is not None

        except Exception as e:
            logger.error(f"Error verifying API key: {e}")
            return False
