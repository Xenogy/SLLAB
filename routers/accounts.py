from fastapi import APIRouter, Request, Depends, HTTPException
from dependencies import get_query_token
from db import conn, get_db_connection, get_user_db_connection
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json
from routers.auth import get_current_active_user
from contextlib import asynccontextmanager

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

class AccountListParams(BaseModel):
    limit: Optional[int] = 100
    offset: Optional[int] = 0
    search: Optional[str] = None
    sort_by: Optional[str] = "acc_id"
    sort_order: Optional[str] = "asc"
    filter_prime: Optional[bool] = None
    filter_lock: Optional[bool] = None
    filter_perm_lock: Optional[bool] = None

class AccountListResponse(BaseModel):
    accounts: List[AccountResponse]
    total: int
    limit: int
    offset: int

router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
    # Remove the dependency on get_query_token as we're using JWT authentication
    # dependencies=[Depends(get_query_token)],
    responses={404: {"description": "Not found"}},
)

@router.post("/list", response_model=AccountListResponse)
async def list_accounts_post(params: AccountListParams, current_user = Depends(get_current_active_user)):
    """Get a list of accounts with pagination, sorting, and filtering (POST method)"""
    return await _list_accounts(params, current_user)

@router.get("/list", response_model=AccountListResponse)
async def list_accounts_get(
    limit: int = 100,
    offset: int = 0,
    search: Optional[str] = None,
    sort_by: str = "acc_id",
    sort_order: str = "asc",
    filter_prime: Optional[bool] = None,
    filter_lock: Optional[bool] = None,
    filter_perm_lock: Optional[bool] = None,
    current_user = Depends(get_current_active_user)
):
    """Get a list of accounts with pagination, sorting, and filtering (GET method)"""
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

@router.get("/{acc_username}", response_model=AccountResponse)
async def get_account(acc_username: str, current_user = Depends(get_current_active_user)):
    """Get basic account information"""
    # Use user-specific database connection with RLS
    with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as user_conn:
        cursor = user_conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    acc_id,
                    acc_username,
                    acc_email_address,
                    prime,
                    lock,
                    perm_lock,
                    acc_created_at
                FROM accounts_with_rls
                WHERE acc_id = %s
            """, (acc_username,))

            result = cursor.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="Account not found")

            account = {
                "acc_id": result[0],
                "acc_username": result[1],
                "acc_email_address": result[2],
                "prime": result[3],
                "lock": result[4],
                "perm_lock": result[5],
                "acc_created_at": result[6]
            }

            return account

        except Exception as e:
            print(f"Error retrieving account: {e}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail="Error retrieving account information")

        finally:
            cursor.close()

@router.post("/info")
async def get_account_info(acc_id: str, datatypes: List[str], current_user = Depends(get_current_active_user)):
    """Get specific account information by field names"""
    # Use user-specific database connection with RLS
    with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as user_conn:
        cursor = user_conn.cursor()

        try:
            # Validate that the requested fields exist in the accounts table
            valid_fields = [
                "acc_id", "acc_username", "acc_password", "acc_email_address",
                "acc_email_password", "acc_vault_address", "acc_vault_password",
                "acc_created_at", "acc_session_start", "acc_steamguard_account_name",
                "acc_confirm_type", "acc_device_id", "acc_identity_secret",
                "acc_revocation_code", "acc_secret_1", "acc_serial_number",
                "acc_server_time", "acc_shared_secret", "acc_status",
                "acc_token_gid", "acc_uri", "id", "prime", "lock", "perm_lock",
                "farmlabs_upload"
            ]

            # Filter out invalid fields
            valid_datatypes = [field for field in datatypes if field in valid_fields]

            if not valid_datatypes:
                raise HTTPException(status_code=400, detail="No valid fields requested")

            # Build and execute the query
            fields_str = ", ".join(valid_datatypes)
            cursor.execute(f"SELECT {fields_str} FROM accounts_with_rls WHERE acc_id = %s", (acc_id,))

            result = cursor.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail="Account not found")

            # Create a dictionary with the requested fields
            response = {}
            for i, field in enumerate(valid_datatypes):
                response[field] = result[i]

            return response

        except Exception as e:
            print(f"Error retrieving account info: {e}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail="Error retrieving account information")

        finally:
            cursor.close()

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
    # Use user-specific database connection with RLS
    with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as user_conn:
        cursor = user_conn.cursor()

        try:
            # Check if the account exists and belongs to the current user (RLS will handle this)
            cursor.execute("SELECT acc_id FROM accounts_with_rls WHERE acc_id = %s", (acc_id,))
            result = cursor.fetchone()

            if not result:
                raise HTTPException(status_code=404, detail="Account not found or you don't have permission to delete it")

            # Delete the account
            cursor.execute("DELETE FROM accounts_with_rls WHERE acc_id = %s RETURNING acc_id", (acc_id,))
            deleted = cursor.fetchone()
            user_conn.commit()

            return {"status": "success", "message": f"Account {acc_id} deleted successfully"}
        except Exception as e:
            user_conn.rollback()
            print(f"Error deleting account: {e}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error deleting account: {str(e)}")
        finally:
            cursor.close()



async def _list_accounts(params: AccountListParams, current_user):
    """Get a list of accounts with pagination, sorting, and filtering"""
    # Use user-specific database connection with RLS
    with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as user_conn:
        cursor = user_conn.cursor()

        try:
            # Validate sort_by field
            valid_sort_fields = [
                "acc_id", "acc_username", "acc_email_address",
                "prime", "lock", "perm_lock", "acc_created_at"
            ]

            if params.sort_by not in valid_sort_fields:
                params.sort_by = "acc_id"

            # Validate sort_order
            if params.sort_order.lower() not in ["asc", "desc"]:
                params.sort_order = "asc"

            # Build the query
            query = """
                SELECT
                    acc_id,
                    acc_username,
                    acc_email_address,
                    prime,
                    lock,
                    perm_lock,
                    acc_created_at
                FROM accounts_with_rls
                WHERE 1=1
            """

            count_query = "SELECT COUNT(*) FROM accounts_with_rls WHERE 1=1"
            query_params = []

            # Add search condition if provided
            if params.search:
                search_condition = "AND (acc_id ILIKE %s OR acc_username ILIKE %s OR acc_email_address ILIKE %s)"
                query += search_condition
                count_query += search_condition
                search_term = f"%{params.search}%"
                query_params.extend([search_term, search_term, search_term])

            # Add filter conditions if provided
            if params.filter_prime is not None:
                query += " AND prime = %s"
                count_query += " AND prime = %s"
                query_params.append(params.filter_prime)

            if params.filter_lock is not None:
                query += " AND lock = %s"
                count_query += " AND lock = %s"
                query_params.append(params.filter_lock)

            if params.filter_perm_lock is not None:
                query += " AND perm_lock = %s"
                count_query += " AND perm_lock = %s"
                query_params.append(params.filter_perm_lock)

            # Add sorting
            query += f" ORDER BY {params.sort_by} {params.sort_order}"

            # Add pagination
            query += " LIMIT %s OFFSET %s"
            query_params.extend([params.limit, params.offset])

            # Get total count
            cursor.execute(count_query, query_params[:-2] if len(query_params) > 2 else query_params)
            total = cursor.fetchone()[0]

            # Execute the main query
            cursor.execute(query, query_params)
            results = cursor.fetchall()

            # Format the results
            accounts = []
            for row in results:
                account = {
                    "acc_id": row[0],
                    "acc_username": row[1],
                    "acc_email_address": row[2],
                    "prime": row[3],
                    "lock": row[4],
                    "perm_lock": row[5],
                    "acc_created_at": row[6]
                }
                accounts.append(account)

            return {
                "accounts": accounts,
                "total": total,
                "limit": params.limit,
                "offset": params.offset
            }

        except Exception as e:
            print(f"Error listing accounts: {e}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Error listing accounts: {str(e)}")

        finally:
            cursor.close()
