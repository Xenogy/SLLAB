"""
Repository for ban check data.

This module provides a repository class for accessing ban check data in the database.
It extends the BaseRepository class and provides methods for accessing ban check tasks and results.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime

from .base import BaseRepository

# Configure logging
logger = logging.getLogger(__name__)

class BanCheckRepository(BaseRepository):
    """Repository for ban check data."""

    def __init__(self, user_id: Optional[int] = None, user_role: Optional[str] = None):
        """
        Initialize the BanCheckRepository instance.

        Args:
            user_id (Optional[int], optional): The ID of the user for RLS context. Defaults to None.
            user_role (Optional[str], optional): The role of the user for RLS context. Defaults to None.
        """
        super().__init__(user_id, user_role)
        self.table_name = "ban_check_tasks"
        self.id_column = "task_id"
        self.default_columns = """
            task_id, status, message, progress, results, proxy_stats,
            created_at, updated_at, owner_id
        """
        self.default_order_by = "created_at DESC"
        self.search_columns = ["task_id", "status", "message"]

    def create_task(self, task_id: str, status: str, message: str, progress: float = 0,
                   results: Optional[List[Dict[str, Any]]] = None,
                   proxy_stats: Optional[Dict[str, Any]] = None,
                   owner_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Create a new ban check task.

        Args:
            task_id (str): The task ID.
            status (str): The task status.
            message (str): The task message.
            progress (float, optional): The task progress. Defaults to 0.
            results (Optional[List[Dict[str, Any]]], optional): The task results. Defaults to None.
            proxy_stats (Optional[Dict[str, Any]], optional): The proxy statistics. Defaults to None.
            owner_id (Optional[int], optional): The owner ID. Defaults to None.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with the created task or None if creation failed.
        """
        try:
            # Prepare data
            data = {
                "task_id": task_id,
                "status": status,
                "message": message,
                "progress": progress,
                "results": json.dumps(results) if results else None,
                "proxy_stats": json.dumps(proxy_stats) if proxy_stats else None,
                "owner_id": owner_id or self.user_id
            }

            # Create task
            task = self.create(data)

            # Parse JSON fields
            if task:
                if task.get("results") and isinstance(task["results"], str):
                    try:
                        task["results"] = json.loads(task["results"])
                    except:
                        task["results"] = None

                if task.get("proxy_stats") and isinstance(task["proxy_stats"], str):
                    try:
                        task["proxy_stats"] = json.loads(task["proxy_stats"])
                    except:
                        task["proxy_stats"] = None

            return task

        except Exception as e:
            logger.error(f"Error creating ban check task: {e}")
            return None

    def update_task(self, task_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a ban check task.

        Args:
            task_id (str): The task ID.
            data (Dict[str, Any]): The data to update.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with the updated task or None if update failed.
        """
        try:
            # Prepare data
            update_data = dict(data)

            # Convert JSON fields
            if "results" in update_data and update_data["results"] is not None:
                update_data["results"] = json.dumps(update_data["results"])

            if "proxy_stats" in update_data and update_data["proxy_stats"] is not None:
                update_data["proxy_stats"] = json.dumps(update_data["proxy_stats"])

            # Update task
            updated = self.update(task_id, update_data, returning=True)

            # Parse JSON fields
            if updated:
                if updated.get("results") and isinstance(updated["results"], str):
                    try:
                        updated["results"] = json.loads(updated["results"])
                    except:
                        updated["results"] = None

                if updated.get("proxy_stats") and isinstance(updated["proxy_stats"], str):
                    try:
                        updated["proxy_stats"] = json.loads(updated["proxy_stats"])
                    except:
                        updated["proxy_stats"] = None

            return updated

        except Exception as e:
            logger.error(f"Error updating ban check task: {e}")
            return None

    def get_task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a ban check task by ID.

        Args:
            task_id (str): The task ID.

        Returns:
            Optional[Dict[str, Any]]: A dictionary with the task or None if not found.
        """
        try:
            # Get task
            task = self.get_by_id(task_id)

            # Parse JSON fields
            if task:
                if task.get("results") and isinstance(task["results"], str):
                    try:
                        task["results"] = json.loads(task["results"])
                    except:
                        task["results"] = None

                if task.get("proxy_stats") and isinstance(task["proxy_stats"], str):
                    try:
                        task["proxy_stats"] = json.loads(task["proxy_stats"])
                    except:
                        task["proxy_stats"] = None

            return task

        except Exception as e:
            logger.error(f"Error getting ban check task: {e}")
            return None

    def get_tasks(self, limit: int = 50, offset: int = 0, status: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a list of ban check tasks with pagination and filtering.

        Args:
            limit (int, optional): The maximum number of tasks to return. Defaults to 50.
            offset (int, optional): The number of tasks to skip. Defaults to 0.
            status (Optional[str], optional): Filter by status. Defaults to None.

        Returns:
            Dict[str, Any]: A dictionary with the tasks and pagination info.
        """
        try:
            # Prepare condition and parameters
            condition = ""
            params = []

            if status:
                condition = "status = %s"
                params = [status]

            # Calculate page number from offset and limit
            page = (offset // limit) + 1 if limit > 0 else 1
            page_size = limit

            # Get tasks using page and page_size instead of limit and offset
            result = self.get_paginated(page=page, page_size=page_size, condition=condition, params=tuple(params) if params else None)

            # Parse JSON fields
            tasks = result.get("items", [])

            # Filter out any invalid task entries (like count objects)
            valid_tasks = []
            for task in tasks:
                # Skip entries that don't have required fields
                if not isinstance(task, dict) or "task_id" not in task or "status" not in task:
                    continue

                # Parse JSON fields
                if task.get("results") and isinstance(task["results"], str):
                    try:
                        task["results"] = json.loads(task["results"])
                    except:
                        task["results"] = None

                if task.get("proxy_stats") and isinstance(task["proxy_stats"], str):
                    try:
                        task["proxy_stats"] = json.loads(task["proxy_stats"])
                    except:
                        task["proxy_stats"] = None

                valid_tasks.append(task)

            return {
                "tasks": valid_tasks,
                "total": result.get("total", 0),
                "limit": limit,
                "offset": offset
            }

        except Exception as e:
            logger.error(f"Error getting ban check tasks: {e}")
            return {
                "tasks": [],
                "total": 0,
                "limit": limit,
                "offset": offset
            }

    def delete_task(self, task_id: str) -> bool:
        """
        Delete a ban check task.

        Args:
            task_id (str): The task ID.

        Returns:
            bool: True if the task was deleted, False otherwise.
        """
        try:
            # Delete task
            result = self.delete(task_id)

            return result > 0

        except Exception as e:
            logger.error(f"Error deleting ban check task: {e}")
            return False
