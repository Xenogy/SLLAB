from fastapi import Depends
from contextlib import asynccontextmanager
from routers.auth import get_current_active_user
from db import get_user_db_connection

@asynccontextmanager
async def get_user_db(current_user = Depends(get_current_active_user)):
    """
    Dependency that provides a database connection with the user context set.
    This ensures that Row Level Security policies are applied correctly.
    """
    user_id = current_user.get("id")
    user_role = current_user.get("role")
    
    # Use the token values if available (as a fallback)
    if user_id is None:
        user_id = current_user.get("token_user_id")
    if user_role is None:
        user_role = current_user.get("token_user_role")
    
    with get_user_db_connection(user_id=user_id, user_role=user_role) as conn:
        yield conn
