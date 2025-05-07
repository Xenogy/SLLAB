"""
Downloads router.

This module provides endpoints for downloading files.
"""

import logging
import os
import shutil
import zipfile
from typing import Dict, Any, Optional, List
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, Response, status
from fastapi.responses import FileResponse, StreamingResponse

from config import Config

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/downloads",
    tags=["downloads"],
    responses={404: {"description": "Not found"}},
)

# Endpoints
@router.get("/test", response_class=FileResponse)
async def download_test_file():
    """
    Download a test file.
    """
    logger.info("Downloading test file")

    # Path to the test file
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "test.txt")

    # Check if the file exists
    if not os.path.exists(file_path):
        # Create a test file if it doesn't exist
        with open(file_path, "w") as f:
            f.write("This is a test file.")

    return FileResponse(
        path=file_path,
        filename="test.txt",
        media_type="text/plain"
    )

@router.get("/windows_vm_agent.zip")
async def download_windows_vm_agent():
    """
    Download the Windows VM agent as a ZIP file.

    This endpoint packages the Windows VM agent files into a ZIP file and returns it.
    """
    logger.info("Downloading Windows VM agent")

    # Path to the Windows VM agent directory
    # Get the absolute path to the project root directory
    project_root = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    agent_dir = os.path.join(project_root, "windows_vm_agent")

    logger.info(f"Looking for Windows VM agent directory at: {agent_dir}")

    # Check if the directory exists
    if not os.path.exists(agent_dir):
        logger.error(f"Windows VM agent directory not found: {agent_dir}")
        raise HTTPException(status_code=404, detail="Windows VM agent not found")

    # Create a ZIP file in memory
    zip_buffer = BytesIO()

    try:
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Walk through the directory and add all files to the ZIP
            for root, dirs, files in os.walk(agent_dir):
                # Skip __pycache__ directories
                if "__pycache__" in root:
                    continue

                # Skip .git directories
                if ".git" in root:
                    continue

                # Skip .egg-info directories
                if ".egg-info" in root:
                    continue

                for file in files:
                    # Skip .pyc files
                    if file.endswith(".pyc"):
                        continue

                    # Skip .git files
                    if ".git" in file:
                        continue

                    # Get the full path of the file
                    file_path = os.path.join(root, file)

                    # Get the relative path for the ZIP file
                    rel_path = os.path.relpath(file_path, os.path.dirname(agent_dir))

                    # Add the file to the ZIP
                    zip_file.write(file_path, rel_path)

        # Reset the buffer position to the beginning
        zip_buffer.seek(0)

        # Return the ZIP file as a streaming response
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=windows_vm_agent.zip"}
        )

    except Exception as e:
        logger.error(f"Error creating Windows VM agent ZIP file: {e}")
        raise HTTPException(status_code=500, detail="Error creating Windows VM agent ZIP file")
