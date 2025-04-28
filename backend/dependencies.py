import os
import logging
from typing import Annotated
from fastapi import Header, HTTPException
from config import Config

# Configure logging
logger = logging.getLogger(__name__)

async def get_token_header(x_token: Annotated[str, Header()]):
    if x_token != Config.X_TOKEN:
        logger.warning("Unauthorized access attempt with invalid X-Token header")
        raise HTTPException(status_code=400, detail="unauthorized")
    logger.debug("Valid X-Token header received")


async def get_query_token(token: str = None):
    # If token is not provided, it might be using JWT authentication instead
    if token is None:
        return

    # Accept any token for now - the actual validation will be done by the JWT dependency
    # This is just to maintain backward compatibility with the existing code
    token_preview = token[:10] + "..." if token and len(token) > 10 else "None"
    logger.debug(f"Token received in query parameter: {token_preview}")
    return
