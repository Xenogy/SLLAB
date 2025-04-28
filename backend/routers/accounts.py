from fastapi import APIRouter, Request, Depends, HTTPException, Query, Path, Body, Response
from fastapi.responses import StreamingResponse
import time
from dependencies import get_query_token
from db import get_db_connection, get_user_db_connection
from db.optimized_queries import (
    build_optimized_search_query,
    build_batch_fetch_query,
    build_cursor_pagination_query,
    build_projection_query,
    build_combined_count_query
)
from db.repositories.accounts import AccountRepository
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
import json
import base64
from routers.auth import get_current_active_user
from contextlib import asynccontextmanager
import logging

# Configure logging
logger = logging.getLogger(__name__)

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

class User(BaseModel):
    username: str
    password: str

class Email(BaseModel):
    address: str
    password: str

class Vault(BaseModel):
    address: str
    password: str

class Metadata(BaseModel):
    createdAt: int
    sessionStart: int
    tags: List[str] = Field(default_factory=list)
    guard: str

class Steamguard(BaseModel):
    deviceId: str
    shared_secret: str
    serial_number: str
    revocation_code: str
    uri: str
    server_time: str
    account_name: str
    token_gid: str
    identity_secret: str
    secret_1: str
    status: int
    confirm_type: int

class ReceivedData(BaseModel):
    id: str
    user: User
    email: Optional[Email] = None
    vault: Vault
    metadata: Metadata
    steamguard: Optional[Steamguard] = None

class AccountResponse(BaseModel):
    acc_id: str
    acc_username: str
    acc_email_address: str
    prime: bool
    lock: bool
    perm_lock: bool
    acc_created_at: int

class AccountCreate(BaseModel):
    acc_id: str = Field(..., description="Steam account ID")
    acc_username: str = Field(..., description="Steam account username")
    acc_password: str = Field(..., description="Steam account password")
    acc_email_address: str = Field(..., description="Email address associated with the account")
    acc_email_password: str = Field(..., description="Password for the email account")
    prime: bool = Field(False, description="Whether the account has Prime status")
    lock: bool = Field(False, description="Whether the account is locked")
    perm_lock: bool = Field(False, description="Whether the account is permanently locked")
    acc_created_at: Optional[float] = Field(None, description="Timestamp when the account was created")

class AccountListParams(BaseModel):
    limit: Optional[int] = 100
    offset: Optional[int] = 0
    search: Optional[str] = None
    sort_by: Optional[str] = "acc_id"
    sort_order: Optional[str] = "asc"
    filter_prime: Optional[bool] = None
    filter_lock: Optional[bool] = None
    filter_perm_lock: Optional[bool] = None
    fields: Optional[List[str]] = None  # For projection support

class CursorPaginationParams(BaseModel):
    cursor: Optional[str] = None
    limit: int = 100
    sort_by: str = "acc_id"
    sort_order: str = "asc"
    search: Optional[str] = None
    filter_prime: Optional[bool] = None
    filter_lock: Optional[bool] = None
    filter_perm_lock: Optional[bool] = None

class AccountListResponse(BaseModel):
    accounts: List[AccountResponse]
    total: int
    limit: int
    offset: Optional[int] = None
    cursor: Optional[str] = None
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None

router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
    # Remove the dependency on get_query_token as we're using JWT authentication
    # dependencies=[Depends(get_query_token)],
    responses={404: {"description": "Not found"}},
)

@router.post("/list", response_model=AccountListResponse,
         summary="List accounts (POST method)",
         description="Get a list of accounts with pagination, sorting, and filtering using POST method",
         responses={
             200: {
                 "description": "List of accounts",
                 "content": {
                     "application/json": {
                         "example": {
                             "accounts": [
                                 {
                                     "acc_id": "76561199123456789",
                                     "acc_username": "steamuser1",
                                     "acc_email_address": "user1@example.com",
                                     "prime": True,
                                     "lock": False,
                                     "perm_lock": False,
                                     "acc_created_at": 1609459200
                                 }
                             ],
                             "total": 1,
                             "limit": 100,
                             "offset": 0
                         }
                     }
                 }
             },
             401: {"description": "Unauthorized"},
             403: {"description": "Forbidden"},
             422: {"description": "Validation Error"}
         })
async def list_accounts_post(
    params: AccountListParams,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get a list of accounts with pagination, sorting, and filtering using POST method.

    This endpoint allows for more complex filtering and sorting options compared to the GET method.

    The response includes:
    - A list of accounts matching the filter criteria
    - The total number of accounts matching the filter criteria
    - The limit and offset parameters used for pagination

    Regular users can only see their own accounts, while administrators can see all accounts.
    """
    return await _list_accounts(params, current_user)

@router.get("/list", response_model=AccountListResponse,
         summary="List accounts (GET method)",
         description="Get a list of accounts with pagination, sorting, and filtering using GET method",
         responses={
             200: {
                 "description": "List of accounts",
                 "content": {
                     "application/json": {
                         "example": {
                             "accounts": [
                                 {
                                     "acc_id": "76561199123456789",
                                     "acc_username": "steamuser1",
                                     "acc_email_address": "user1@example.com",
                                     "prime": True,
                                     "lock": False,
                                     "perm_lock": False,
                                     "acc_created_at": 1609459200
                                 }
                             ],
                             "total": 1,
                             "limit": 100,
                             "offset": 0
                         }
                     }
                 }
             },
             401: {"description": "Unauthorized"},
             403: {"description": "Forbidden"},
             422: {"description": "Validation Error"}
         })
async def list_accounts_get(
    limit: int = Query(100, description="Maximum number of accounts to return", ge=1, le=1000),
    offset: int = Query(0, description="Number of accounts to skip", ge=0),
    search: Optional[str] = Query(None, description="Search term to filter accounts by username or email"),
    sort_by: str = Query("acc_id", description="Field to sort by"),
    sort_order: str = Query("asc", description="Sort order (asc or desc)"),
    filter_prime: Optional[bool] = Query(None, description="Filter by prime status"),
    filter_lock: Optional[bool] = Query(None, description="Filter by lock status"),
    filter_perm_lock: Optional[bool] = Query(None, description="Filter by permanent lock status"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get a list of accounts with pagination, sorting, and filtering using GET method.

    This endpoint provides a RESTful way to retrieve accounts with various filter options.

    The response includes:
    - A list of accounts matching the filter criteria
    - The total number of accounts matching the filter criteria
    - The limit and offset parameters used for pagination

    Regular users can only see their own accounts, while administrators can see all accounts.

    ## Query Parameters

    - **limit**: Maximum number of accounts to return (default: 100)
    - **offset**: Number of accounts to skip (default: 0)
    - **search**: Search term to filter accounts by username or email
    - **sort_by**: Field to sort by (default: acc_id)
    - **sort_order**: Sort order (asc or desc) (default: asc)
    - **filter_prime**: Filter by prime status (true/false)
    - **filter_lock**: Filter by lock status (true/false)
    - **filter_perm_lock**: Filter by permanent lock status (true/false)
    """
    params = AccountListParams(
        limit=limit,
        offset=offset,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        filter_prime=filter_prime,
        filter_lock=filter_lock,
        filter_perm_lock=filter_perm_lock
    )
    return await _list_accounts(params, current_user)

@router.get("/list/cursor", response_model=AccountListResponse,
         summary="List accounts with cursor-based pagination",
         description="Get a list of accounts using cursor-based pagination for better performance with large datasets",
         responses={
             200: {
                 "description": "List of accounts",
                 "content": {
                     "application/json": {
                         "example": {
                             "accounts": [
                                 {
                                     "acc_id": "76561199123456789",
                                     "acc_username": "steamuser1",
                                     "acc_email_address": "user1@example.com",
                                     "prime": True,
                                     "lock": False,
                                     "perm_lock": False,
                                     "acc_created_at": 1609459200
                                 }
                             ],
                             "total": 1,
                             "limit": 100,
                             "cursor": None,
                             "next_cursor": "eyJhY2NfaWQiOiI3NjU2MTE5OTEyMzQ1Njc4OSJ9"
                         }
                     }
                 }
             },
             401: {"description": "Unauthorized"},
             403: {"description": "Forbidden"},
             422: {"description": "Validation Error"}
         })
async def list_accounts_cursor(
    cursor: Optional[str] = Query(None, description="Cursor for pagination"),
    limit: int = Query(100, description="Maximum number of accounts to return", ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search term to filter accounts by username or email"),
    sort_by: str = Query("acc_id", description="Field to sort by"),
    sort_order: str = Query("asc", description="Sort order (asc or desc)"),
    filter_prime: Optional[bool] = Query(None, description="Filter by prime status"),
    filter_lock: Optional[bool] = Query(None, description="Filter by lock status"),
    filter_perm_lock: Optional[bool] = Query(None, description="Filter by permanent lock status"),
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    response: Response = None
):
    """
    Get a list of accounts using cursor-based pagination.

    This endpoint provides cursor-based pagination for better performance with large datasets.

    The response includes:
    - A list of accounts matching the filter criteria
    - The total number of accounts matching the filter criteria
    - The limit parameter used for pagination
    - The cursor used for this request
    - The next cursor to use for the next page

    Regular users can only see their own accounts, while administrators can see all accounts.

    ## Query Parameters

    - **cursor**: Cursor for pagination (optional)
    - **limit**: Maximum number of accounts to return (default: 100)
    - **search**: Search term to filter accounts by username or email
    - **sort_by**: Field to sort by (default: acc_id)
    - **sort_order**: Sort order (asc or desc) (default: asc)
    - **filter_prime**: Filter by prime status (true/false)
    - **filter_lock**: Filter by lock status (true/false)
    - **filter_perm_lock**: Filter by permanent lock status (true/false)
    """
    # Use the repository pattern with RLS context
    account_repo = AccountRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Decode cursor if provided
        cursor_value = None
        if cursor:
            try:
                cursor_data = json.loads(base64.b64decode(cursor).decode('utf-8'))
                cursor_value = cursor_data.get(sort_by)
            except Exception as e:
                logger.error(f"Error decoding cursor: {e}", exc_info=True)
                raise HTTPException(status_code=400, detail="Invalid cursor format")

        # Build filter conditions
        filter_conditions = {}
        if filter_prime is not None:
            filter_conditions["prime"] = filter_prime
        if filter_lock is not None:
            filter_conditions["lock"] = filter_lock
        if filter_perm_lock is not None:
            filter_conditions["perm_lock"] = filter_perm_lock

        # Get accounts with cursor-based pagination
        result = account_repo.get_accounts_with_cursor(
            cursor_value=cursor_value,
            cursor_column=sort_by,
            sort_order=sort_order,
            limit=limit,
            filter_conditions=filter_conditions
        )

        # Generate next cursor if there are more results
        next_cursor = None
        if result["has_more"] and result["accounts"]:
            last_item = result["accounts"][-1]
            cursor_data = {sort_by: last_item[sort_by.replace("acc_", "") if sort_by.startswith("acc_") else sort_by]}
            next_cursor = base64.b64encode(json.dumps(cursor_data).encode('utf-8')).decode('utf-8')

        # Set cache headers if response is provided
        if response:
            response.headers["Cache-Control"] = "max-age=60, public"

        return {
            "accounts": result["accounts"],
            "total": result["total"],
            "limit": limit,
            "cursor": cursor,
            "next_cursor": next_cursor
        }

    except Exception as e:
        logger.error(f"Error listing accounts with cursor: {e}", exc_info=True)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error listing accounts: {str(e)}")

@router.get("/list/fields", response_model=Dict[str, Any],
         summary="List accounts with field selection",
         description="Get a list of accounts with field selection (projection) for better performance",
         responses={
             200: {
                 "description": "List of accounts with selected fields",
                 "content": {
                     "application/json": {
                         "example": {
                             "accounts": [
                                 {
                                     "acc_id": "76561199123456789",
                                     "acc_username": "steamuser1"
                                 }
                             ],
                             "total": 1,
                             "limit": 100,
                             "offset": 0
                         }
                     }
                 }
             },
             401: {"description": "Unauthorized"},
             403: {"description": "Forbidden"},
             422: {"description": "Validation Error"}
         })
async def list_accounts_fields(
    fields: str = Query("acc_id,acc_username,acc_email_address", description="Comma-separated list of fields to include"),
    limit: int = Query(100, description="Maximum number of accounts to return", ge=1, le=1000),
    offset: int = Query(0, description="Number of accounts to skip", ge=0),
    search: Optional[str] = Query(None, description="Search term to filter accounts by username or email"),
    sort_by: str = Query("acc_id", description="Field to sort by"),
    sort_order: str = Query("asc", description="Sort order (asc or desc)"),
    filter_prime: Optional[bool] = Query(None, description="Filter by prime status"),
    filter_lock: Optional[bool] = Query(None, description="Filter by lock status"),
    filter_perm_lock: Optional[bool] = Query(None, description="Filter by permanent lock status"),
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    response: Response = None
):
    """
    Get a list of accounts with field selection (projection).

    This endpoint allows you to specify which fields to include in the response,
    which can improve performance for large datasets.

    The response includes:
    - A list of accounts with the selected fields
    - The total number of accounts matching the filter criteria
    - The limit and offset parameters used for pagination

    Regular users can only see their own accounts, while administrators can see all accounts.

    ## Query Parameters

    - **fields**: Comma-separated list of fields to include (default: acc_id,acc_username,acc_email_address)
    - **limit**: Maximum number of accounts to return (default: 100)
    - **offset**: Number of accounts to skip (default: 0)
    - **search**: Search term to filter accounts by username or email
    - **sort_by**: Field to sort by (default: acc_id)
    - **sort_order**: Sort order (asc or desc) (default: asc)
    - **filter_prime**: Filter by prime status (true/false)
    - **filter_lock**: Filter by lock status (true/false)
    - **filter_perm_lock**: Filter by permanent lock status (true/false)
    """
    # Parse fields
    field_list = fields.split(",")

    # Validate fields
    valid_fields = [
        "acc_id", "acc_username", "acc_email_address",
        "prime", "lock", "perm_lock", "acc_created_at"
    ]
    selected_fields = [field for field in field_list if field in valid_fields]

    # Ensure acc_id is always included
    if "acc_id" not in selected_fields:
        selected_fields.append("acc_id")

    # Use the repository pattern with RLS context
    account_repo = AccountRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Get accounts with pagination, sorting, and filtering
        result = account_repo.get_accounts(
            limit=limit,
            offset=offset,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            filter_prime=filter_prime,
            filter_lock=filter_lock,
            filter_perm_lock=filter_perm_lock
        )

        # Set cache headers if response is provided
        if response:
            response.headers["Cache-Control"] = "max-age=60, public"

        # Filter the accounts to only include the selected fields
        filtered_accounts = []
        for account in result["accounts"]:
            filtered_account = {}
            for field in selected_fields:
                if field in account:
                    filtered_account[field] = account[field]
            filtered_accounts.append(filtered_account)

        return {
            "accounts": filtered_accounts,
            "total": result["total"],
            "limit": result["limit"],
            "offset": result["offset"]
        }

    except Exception as e:
        logger.error(f"Error listing accounts with field selection: {e}", exc_info=True)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error listing accounts: {str(e)}")

@router.get("/list/stream")
async def list_accounts_stream(
    limit: int = Query(1000, description="Maximum number of accounts to return", ge=1, le=10000),
    search: Optional[str] = Query(None, description="Search term to filter accounts by username or email"),
    sort_by: str = Query("acc_id", description="Field to sort by"),
    sort_order: str = Query("asc", description="Sort order (asc or desc)"),
    filter_prime: Optional[bool] = Query(None, description="Filter by prime status"),
    filter_lock: Optional[bool] = Query(None, description="Filter by lock status"),
    filter_perm_lock: Optional[bool] = Query(None, description="Filter by permanent lock status"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Stream a list of accounts as JSON.

    This endpoint streams the results as they are fetched from the database,
    which is more efficient for large datasets.

    Regular users can only see their own accounts, while administrators can see all accounts.

    ## Query Parameters

    - **limit**: Maximum number of accounts to return (default: 1000, max: 10000)
    - **search**: Search term to filter accounts by username or email
    - **sort_by**: Field to sort by (default: acc_id)
    - **sort_order**: Sort order (asc or desc) (default: asc)
    - **filter_prime**: Filter by prime status (true/false)
    - **filter_lock**: Filter by lock status (true/false)
    - **filter_perm_lock**: Filter by permanent lock status (true/false)
    """
    return StreamingResponse(
        stream_accounts(
            limit=limit,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            filter_prime=filter_prime,
            filter_lock=filter_lock,
            filter_perm_lock=filter_perm_lock,
            current_user=current_user
        ),
        media_type="application/json"
    )

async def stream_accounts(
    limit: int,
    search: Optional[str],
    sort_by: str,
    sort_order: str,
    filter_prime: Optional[bool],
    filter_lock: Optional[bool],
    filter_perm_lock: Optional[bool],
    current_user: Dict[str, Any]
):
    """Stream accounts as JSON"""
    # Use the repository pattern with RLS context
    account_repo = AccountRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Build filter conditions
        filter_conditions = {}
        if filter_prime is not None:
            filter_conditions["prime"] = filter_prime
        if filter_lock is not None:
            filter_conditions["lock"] = filter_lock
        if filter_perm_lock is not None:
            filter_conditions["perm_lock"] = filter_perm_lock

        # Get accounts with pagination, sorting, and filtering
        result = account_repo.get_accounts(
            limit=limit,
            offset=0,  # Start from the beginning
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            filter_prime=filter_prime,
            filter_lock=filter_lock,
            filter_perm_lock=filter_perm_lock
        )

        # Yield opening bracket
        yield "{"
        yield '"accounts": ['

        # Yield accounts
        first = True
        for account in result["accounts"]:
            if not first:
                yield ","
            first = False

            yield json.dumps(account)

        # Yield closing brackets
        yield "]"
        yield "}"

    except Exception as e:
        logger.error(f"Error streaming accounts: {e}", exc_info=True)
        yield json.dumps({"error": str(e)})

@router.post("/", response_model=AccountResponse, status_code=201,
         summary="Create a new account",
         description="Create a new Steam account in the database",
         responses={
             201: {
                 "description": "Account created successfully",
                 "content": {
                     "application/json": {
                         "example": {
                             "account": {
                                 "acc_id": "76561199123456789",
                                 "acc_username": "steamuser1",
                                 "acc_email_address": "user1@example.com",
                                 "prime": True,
                                 "lock": False,
                                 "perm_lock": False,
                                 "acc_created_at": 1609459200
                             }
                         }
                     }
                 }
             },
             400: {"description": "Bad Request - Account with this ID already exists"},
             401: {"description": "Unauthorized"},
             422: {"description": "Validation Error"}
         })
async def create_account(
    account: AccountCreate = Body(...,
        description="Account details to create",
        example={
            "acc_id": "76561199123456789",
            "acc_username": "steamuser1",
            "acc_password": "password123",
            "acc_email_address": "user1@example.com",
            "acc_email_password": "emailpass123",
            "prime": False,
            "lock": False,
            "perm_lock": False,
            "acc_created_at": None  # Will use current timestamp if null
        }
    ),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Create a new Steam account in the database.

    This endpoint allows users to create a new Steam account record. The account will be
    associated with the current authenticated user.

    ## Request Body

    - **acc_id**: Steam account ID (required)
    - **acc_username**: Steam account username (required)
    - **acc_password**: Steam account password (required)
    - **acc_email_address**: Email address associated with the account (required)
    - **acc_email_password**: Password for the email account (required)
    - **prime**: Whether the account has Prime status (default: false)
    - **lock**: Whether the account is locked (default: false)
    - **perm_lock**: Whether the account is permanently locked (default: false)
    - **acc_created_at**: Timestamp when the account was created (default: current time)

    ## Response

    Returns a JSON object containing the created account details.

    ## Errors

    - **400 Bad Request**: If an account with the same ID already exists
    - **401 Unauthorized**: If the user is not authenticated
    - **422 Validation Error**: If the request body is invalid
    """
    # Use the repository pattern with RLS context
    account_repo = AccountRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Check if account already exists
        existing_account = account_repo.get_account_by_id(account.acc_id)
        if existing_account:
            raise HTTPException(status_code=400, detail="Account with this ID already exists")

        # Prepare account data
        account_data = {
            "acc_id": account.acc_id,
            "acc_username": account.acc_username,
            "acc_password": account.acc_password,
            "acc_email_address": account.acc_email_address,
            "acc_email_password": account.acc_email_password,
            "prime": account.prime,
            "lock": account.lock,
            "perm_lock": account.perm_lock,
            "acc_created_at": account.acc_created_at or time.time(),
            "owner_id": current_user["id"]  # Set the owner_id to the current user's ID
        }

        # Create the account
        created_account = account_repo.create_account(account_data)

        if not created_account:
            raise HTTPException(status_code=500, detail="Failed to create account")

        return {"account": created_account}

    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        logger.error(f"Error creating account: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/{acc_username}", response_model=AccountResponse,
         summary="Get account by username",
         description="Get detailed information about a specific account by its username",
         responses={
             200: {
                 "description": "Account details",
                 "content": {
                     "application/json": {
                         "example": {
                             "account": {
                                 "acc_id": "76561199123456789",
                                 "acc_username": "steamuser1",
                                 "acc_email_address": "user1@example.com",
                                 "prime": True,
                                 "lock": False,
                                 "perm_lock": False,
                                 "acc_created_at": 1609459200
                             }
                         }
                     }
                 }
             },
             401: {"description": "Unauthorized"},
             403: {"description": "Forbidden - You don't have permission to access this account"},
             404: {"description": "Account not found"}
         })
async def get_account(
    acc_username: str = Path(..., description="The username of the account to retrieve"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get detailed information about a specific account by its username.

    This endpoint returns details about a specific account. Regular users can only
    access their own accounts, while administrators can access any account.

    ## Path Parameters

    - **acc_username**: The username of the account to retrieve

    ## Response

    Returns a JSON object containing the account details, including:
    - Account ID
    - Username
    - Email address
    - Prime status
    - Lock status
    - Permanent lock status
    - Creation timestamp

    ## Errors

    - **401 Unauthorized**: If the user is not authenticated
    - **403 Forbidden**: If the user doesn't have permission to access this account
    - **404 Not Found**: If the account doesn't exist
    """
    # Use the repository pattern with RLS context
    account_repo = AccountRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Get the account by username
        account = account_repo.get_account_by_username(acc_username)

        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        return account

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Error retrieving account: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error retrieving account information")

@router.post("/info")
async def get_account_info(acc_id: str, datatypes: List[str], current_user = Depends(get_current_active_user)):
    """Get specific account information by field names"""
    # Use the repository pattern with RLS context
    account_repo = AccountRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Get account info with specific fields
        account_info = account_repo.get_account_info(acc_id, datatypes)

        if not account_info:
            raise HTTPException(status_code=404, detail="Account not found")

        return account_info

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Error retrieving account info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error retrieving account information")

@router.post("/new")
async def new_account(request: Request, debug: bool = False, current_user = Depends(get_current_active_user)):
    """Create a new account from JSON data"""
    try:
        accObject = await request.json()

        # Extract basic account information
        accId = accObject["id"]

        # Extract user information
        accUser = accObject["user"]
        accUsername = accUser["username"]
        accPassword = accUser["password"]

        # Extract email information
        accEmail = accObject["email"]
        accEmailAddress = accEmail["address"]
        accEmailPassword = accEmail["password"]

        # Extract vault information
        accVault = accObject["vault"]
        accVaultAddress = accVault["address"]
        accVaultPassword = accVault["password"]

        # Extract metadata
        accMetadata = accObject["metadata"]
        accCreatedAt = accMetadata["createdAt"]
        accSessionStart = accMetadata["sessionStart"]

        # Debug mode - just print the data and return
        if debug:
            print(f"Debug:\n{accObject}")
            return {"status": "debug", "message": "Debug mode, no account created"}

        # Skip test emails
        if "@demoemail.com" in accEmailAddress:
            print(f'Received test webhook with account object:\n{accObject}')
            return {"status": "skipped", "message": "Test email detected, no account created"}

        # Initialize Steam Guard fields
        accSteamguardAccountName = None
        accConfirmType = None
        accDeviceId = None
        accIdentitySecret = None
        accRevocationCode = None
        accSecret1 = None
        accSerialNumber = None
        accServerTime = None
        accSharedSecret = None
        accStatus = None
        accTokenGid = None
        accUri = None

        # Extract Steam Guard information if available
        if "steamguard" in accObject:
            accSteamguard = accObject["steamguard"]
            accSteamguardAccountName = accSteamguard.get("account_name")
            accConfirmType = accSteamguard.get("confirm_type")
            accDeviceId = accSteamguard.get("deviceId")
            accIdentitySecret = accSteamguard.get("identity_secret")
            accRevocationCode = accSteamguard.get("revocation_code")
            accSecret1 = accSteamguard.get("secret_1")
            accSerialNumber = accSteamguard.get("serial_number")
            accServerTime = accSteamguard.get("server_time")
            accSharedSecret = accSteamguard.get("shared_secret")
            accStatus = accSteamguard.get("status")
            accTokenGid = accSteamguard.get("token_gid")
            accUri = accSteamguard.get("uri")

        print(f'Received new account: ({accUsername} : {accEmailAddress})')

        # Use user-specific database connection with RLS
        with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as user_conn:
            cursor = user_conn.cursor()

            try:
                sql = """
                INSERT INTO accounts (
                    acc_id,
                    acc_username,
                    acc_password,
                    acc_email_address,
                    acc_email_password,
                    acc_vault_address,
                    acc_vault_password,
                    acc_created_at,
                    acc_session_start,
                    acc_steamguard_account_name,
                    acc_confirm_type,
                    acc_device_id,
                    acc_identity_secret,
                    acc_revocation_code,
                    acc_secret_1,
                    acc_serial_number,
                    acc_server_time,
                    acc_shared_secret,
                    acc_status,
                    acc_token_gid,
                    acc_uri,
                    owner_id
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (acc_id) DO UPDATE SET
                    acc_username = EXCLUDED.acc_username,
                    acc_password = EXCLUDED.acc_password,
                    acc_email_address = EXCLUDED.acc_email_address,
                    acc_email_password = EXCLUDED.acc_email_password,
                    acc_vault_address = EXCLUDED.acc_vault_address,
                    acc_vault_password = EXCLUDED.acc_vault_password
                RETURNING acc_id;
                """

                params = (
                    accId,
                    accUsername,
                    accPassword,
                    accEmailAddress,
                    accEmailPassword,
                    accVaultAddress,
                    accVaultPassword,
                    accCreatedAt,
                    accSessionStart,
                    accSteamguardAccountName,
                    accConfirmType,
                    accDeviceId,
                    accIdentitySecret,
                    accRevocationCode,
                    accSecret1,
                    accSerialNumber,
                    accServerTime,
                    accSharedSecret,
                    accStatus,
                    accTokenGid,
                    accUri,
                    current_user["id"]  # Set the owner_id to the current user's ID
                )

                cursor.execute(sql, params)
                result = cursor.fetchone()
                user_conn.commit()

                return {"status": "success", "acc_id": accId, "created": result is not None}

            except Exception as e:
                user_conn.rollback()
                print(f"Error creating account: {e}")
                raise HTTPException(status_code=500, detail=f"Error creating account: {str(e)}")
            finally:
                cursor.close()

    except Exception as e:
        print(f"Error processing account data: {e}")
        raise HTTPException(status_code=400, detail=f"Error processing account data: {str(e)}")

@router.post("/new/bulk")
async def new_bulk_accounts(accounts: List[ReceivedData], debug: bool = False, current_user = Depends(get_current_active_user)):
    """Create multiple accounts at once"""
    if debug:
        print(f"Debug mode: {len(accounts)} accounts received")
        return {"status": "debug", "message": "Debug mode, no accounts created"}

    created_accounts = []
    skipped_accounts = []
    total_accounts = len(accounts)

    # Use user-specific database connection with RLS
    with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as user_conn:
        cursor = user_conn.cursor()

        try:
            for accObject in accounts:
                # Skip test emails
                try:
                    if "@demoemail.com" in accObject.email.address:
                        skipped_accounts.append(accObject.id)
                        continue

                    # Extract account data
                    accId = accObject.id
                    accUsername = accObject.user.username
                    accPassword = accObject.user.password
                    accEmailAddress = accObject.email.address
                    accEmailPassword = accObject.email.password
                    accVaultAddress = accObject.vault.address
                    accVaultPassword = accObject.vault.password
                    accCreatedAt = accObject.metadata.createdAt
                    accSessionStart = accObject.metadata.sessionStart

                    # Initialize Steam Guard fields
                    accSteamguardAccountName = None
                    accConfirmType = None
                    accDeviceId = None
                    accIdentitySecret = None
                    accRevocationCode = None
                    accSecret1 = None
                    accSerialNumber = None
                    accServerTime = None
                    accSharedSecret = None
                    accStatus = None
                    accTokenGid = None
                    accUri = None

                    # Extract Steam Guard information if available
                    if accObject.steamguard:
                        accSteamguardAccountName = accObject.steamguard.account_name
                        accConfirmType = accObject.steamguard.confirm_type
                        accDeviceId = accObject.steamguard.deviceId
                        accIdentitySecret = accObject.steamguard.identity_secret
                        accRevocationCode = accObject.steamguard.revocation_code
                        accSecret1 = accObject.steamguard.secret_1
                        accSerialNumber = accObject.steamguard.serial_number
                        accServerTime = accObject.steamguard.server_time
                        accSharedSecret = accObject.steamguard.shared_secret
                        accStatus = accObject.steamguard.status
                        accTokenGid = accObject.steamguard.token_gid
                        accUri = accObject.steamguard.uri

                    # Insert the account into the database
                    sql = """
                    INSERT INTO accounts (
                        acc_id,
                        acc_username,
                        acc_password,
                        acc_email_address,
                        acc_email_password,
                        acc_vault_address,
                        acc_vault_password,
                        acc_created_at,
                        acc_session_start,
                        acc_steamguard_account_name,
                        acc_confirm_type,
                        acc_device_id,
                        acc_identity_secret,
                        acc_revocation_code,
                        acc_secret_1,
                        acc_serial_number,
                        acc_server_time,
                        acc_shared_secret,
                        acc_status,
                        acc_token_gid,
                        acc_uri,
                        owner_id
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (acc_id) DO UPDATE SET
                        acc_username = EXCLUDED.acc_username,
                        acc_password = EXCLUDED.acc_password,
                        acc_email_address = EXCLUDED.acc_email_address,
                        acc_email_password = EXCLUDED.acc_email_password,
                        acc_vault_address = EXCLUDED.acc_vault_address,
                        acc_vault_password = EXCLUDED.acc_vault_password
                    RETURNING acc_id;
                    """

                    params = (
                        accId,
                        accUsername,
                        accPassword,
                        accEmailAddress,
                        accEmailPassword,
                        accVaultAddress,
                        accVaultPassword,
                        accCreatedAt,
                        accSessionStart,
                        accSteamguardAccountName,
                        accConfirmType,
                        accDeviceId,
                        accIdentitySecret,
                        accRevocationCode,
                        accSecret1,
                        accSerialNumber,
                        accServerTime,
                        accSharedSecret,
                        accStatus,
                        accTokenGid,
                        accUri,
                        current_user["id"]  # Set the owner_id to the current user's ID
                    )

                    cursor.execute(sql, params)
                    result = cursor.fetchone()

                    if result:
                        created_accounts.append(accId)
                except Exception as e:
                    print(f"Error processing account data: {e}")
                    skipped_accounts.append(accObject.id)

            user_conn.commit()
            return {
                "status": "success",
                "created_count": len(created_accounts),
                "created_accounts": created_accounts,
                "skipped_count": len(skipped_accounts),
                "skipped_accounts": skipped_accounts
            }

        except Exception as e:
            user_conn.rollback()
            print(f"Error creating accounts: {e}")
            raise HTTPException(status_code=500, detail=f"Error creating accounts: {str(e)}")
        finally:
            cursor.close()

@router.delete("/{acc_id}")
async def delete_account(acc_id: str, current_user = Depends(get_current_active_user)):
    """Delete an account"""
    # Use the repository pattern with RLS context
    account_repo = AccountRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Check if the account exists and belongs to the current user
        existing_account = account_repo.get_account_by_id(acc_id)

        if not existing_account:
            raise HTTPException(status_code=404, detail="Account not found or you don't have permission to delete it")

        # Delete the account
        success = account_repo.delete_account(acc_id)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete account")

        return {"status": "success", "message": f"Account {acc_id} deleted successfully"}

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Error deleting account: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting account: {str(e)}")



async def _list_accounts(params: AccountListParams, current_user):
    """
    Get a list of accounts with pagination, sorting, and filtering.

    This function uses the repository pattern for better maintainability.
    """
    # Use the repository pattern with RLS context
    account_repo = AccountRepository(user_id=current_user["id"], user_role=current_user["role"])

    try:
        # Get accounts with pagination, sorting, and filtering
        result = account_repo.get_accounts(
            limit=params.limit,
            offset=params.offset,
            search=params.search,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
            filter_prime=params.filter_prime,
            filter_lock=params.filter_lock,
            filter_perm_lock=params.filter_perm_lock
        )

        return result

    except Exception as e:
        logger.error(f"Error listing accounts: {e}", exc_info=True)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error listing accounts: {str(e)}")
