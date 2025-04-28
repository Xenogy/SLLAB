from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from fastapi.responses import JSONResponse
from dependencies import get_query_token
from db import get_user_db_connection
from typing import List, Dict, Any, Optional
import json
import csv
import io
from pydantic import BaseModel, Field, ValidationError
import traceback
import logging
from routers.auth import get_current_active_user

# Import models from accounts router
from routers.accounts import User, Email, Vault, Metadata, Steamguard, ReceivedData

# Import validation functions
from validation import (
    validate_file, validate_account_data, MAX_FILE_SIZE, ALLOWED_FILE_TYPES
)
from middleware.validation import validate_file_upload

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/upload",
    tags=["upload"],
    # Remove the dependency on get_query_token as we're using JWT authentication
    # dependencies=[Depends(get_query_token)],
    responses={404: {"description": "Not found"}},
)

class ValidationErrorDetail(BaseModel):
    """Model for validation error details"""
    loc: List[str]
    msg: str
    type: str

class AccountValidationError(BaseModel):
    """Model for account validation errors"""
    account_id: Optional[str] = None
    row_number: Optional[int] = None
    errors: List[ValidationErrorDetail]

class UploadResponse(BaseModel):
    """Response model for upload endpoints"""
    status: str
    message: str
    total_processed: int
    successful_count: int
    failed_count: int
    successful_accounts: List[str]
    failed_accounts: List[AccountValidationError]

def process_account_data(account_data: Dict[Any, Any], row_number: Optional[int] = None, current_user: dict = None) -> Dict[str, Any]:
    """
    Process and validate account data

    Args:
        account_data: Dictionary containing account data
        row_number: Row number in CSV file (if applicable)
        current_user: The current authenticated user

    Returns:
        Dictionary with validation result
    """
    account_id = account_data.get("id", None)
    row_info = f" (row {row_number})" if row_number is not None else ""

    logger.info(f"Processing account data for account ID: {account_id}{row_info}")

    try:
        # Validate the data using Pydantic model
        try:
            validated_data = ReceivedData(**account_data)
        except ValidationError as e:
            logger.warning(f"Validation error for account ID: {account_id}{row_info}: {e}")
            raise

        logger.debug(f"Account data validated successfully for account ID: {account_id}{row_info}")

        # Use user-specific database connection with RLS
        with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as user_conn:
            if not user_conn:
                logger.error(f"Failed to get database connection for account ID: {account_id}{row_info}")
                raise Exception("Database connection failed")

            cursor = user_conn.cursor()

            try:
                # Extract account data
                accId = validated_data.id
                accUsername = validated_data.user.username
                accPassword = validated_data.user.password

                # Email might be optional in some cases
                accEmailAddress = None
                accEmailPassword = None
                if validated_data.email:
                    accEmailAddress = validated_data.email.address
                    accEmailPassword = validated_data.email.password

                accVaultAddress = validated_data.vault.address
                accVaultPassword = validated_data.vault.password
                accCreatedAt = validated_data.metadata.createdAt
                accSessionStart = validated_data.metadata.sessionStart

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
                if validated_data.steamguard:
                    accSteamguardAccountName = validated_data.steamguard.account_name
                    accConfirmType = validated_data.steamguard.confirm_type
                    accDeviceId = validated_data.steamguard.deviceId
                    accIdentitySecret = validated_data.steamguard.identity_secret
                    accRevocationCode = validated_data.steamguard.revocation_code
                    accSecret1 = validated_data.steamguard.secret_1
                    accSerialNumber = validated_data.steamguard.serial_number
                    accServerTime = validated_data.steamguard.server_time
                    accSharedSecret = validated_data.steamguard.shared_secret
                    accStatus = validated_data.steamguard.status
                    accTokenGid = validated_data.steamguard.token_gid
                    accUri = validated_data.steamguard.uri

                # Skip test emails
                if accEmailAddress and "@demoemail.com" in accEmailAddress:
                    return {
                        "success": False,
                        "account_id": accId,
                        "row_number": row_number,
                        "errors": [
                            ValidationErrorDetail(
                                loc=["email", "address"],
                                msg="Test email detected, account skipped",
                                type="value_error"
                            )
                        ]
                    }

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
                user_conn.commit()

                return {
                    "success": True,
                    "account_id": accId
                }

            except Exception as e:
                user_conn.rollback()
                logger.error(f"Error creating account {account_id}{row_info}: {e}")
                logger.error(traceback.format_exc())

                return {
                    "success": False,
                    "account_id": account_id,
                    "row_number": row_number,
                    "errors": [
                        ValidationErrorDetail(
                            loc=["database"],
                            msg=f"Database error: {str(e)}",
                            type="db_error"
                        )
                    ]
                }
            finally:
                cursor.close()

    except ValidationError as e:
        # Convert Pydantic validation errors to our format
        errors = []
        for error in e.errors():
            errors.append(
                ValidationErrorDetail(
                    loc=[str(loc) for loc in error["loc"]],
                    msg=error["msg"],
                    type=error["type"]
                )
            )

        return {
            "success": False,
            "account_id": account_id,
            "row_number": row_number,
            "errors": errors
        }
    except Exception as e:
        logger.error(f"Error processing account data {account_id}{row_info}: {e}")
        logger.error(traceback.format_exc())

        return {
            "success": False,
            "account_id": account_id,
            "row_number": row_number,
            "errors": [
                ValidationErrorDetail(
                    loc=["unknown"],
                    msg=f"Unexpected error: {str(e)}",
                    type="unknown_error"
                )
            ]
        }

@router.post("/json", response_model=UploadResponse)
async def upload_json_file(file: UploadFile = File(...), current_user = Depends(get_current_active_user)):
    """
    Upload a JSON file containing account data

    The JSON file should contain an array of account objects or a single account object.
    Each account object should follow the structure defined in the ReceivedData model.
    """
    # Validate file type
    if not file.filename.endswith('.json'):
        logger.warning(f"Invalid file format: {file.filename}")
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a JSON file.")

    # Validate content type
    content_type = file.content_type
    if content_type not in ALLOWED_FILE_TYPES['json']:
        logger.warning(f"Invalid content type: {content_type}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type: {content_type}. Allowed types: {', '.join(ALLOWED_FILE_TYPES['json'])}"
        )

    try:
        # Read the file
        contents = await file.read()

        # Validate file size
        if len(contents) > MAX_FILE_SIZE:
            logger.warning(f"File too large: {len(contents)} bytes")
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024} MB"
            )

        # Parse JSON
        try:
            json_data = json.loads(contents.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

        # Handle both single account and array of accounts
        accounts_data = json_data if isinstance(json_data, list) else [json_data]

        # Validate number of accounts
        if len(accounts_data) > 1000:
            logger.warning(f"Too many accounts: {len(accounts_data)}")
            raise HTTPException(
                status_code=400,
                detail=f"Too many accounts. Maximum: 1000, got {len(accounts_data)}"
            )

        successful_accounts = []
        failed_accounts = []

        # Process each account
        for account_data in accounts_data:
            # Validate account data
            validation_result = validate_account_data(account_data)
            if not validation_result.valid:
                logger.warning(f"Invalid account data: {validation_result.errors}")
                failed_accounts.append(
                    AccountValidationError(
                        account_id=account_data.get("id"),
                        errors=[
                            ValidationErrorDetail(
                                loc=error["field"].split("."),
                                msg=error["message"],
                                type="validation_error"
                            ) for error in validation_result.errors
                        ]
                    )
                )
                continue

            # Process valid account data
            result = process_account_data(account_data, current_user=current_user)

            if result["success"]:
                successful_accounts.append(result["account_id"])
            else:
                failed_accounts.append(
                    AccountValidationError(
                        account_id=result.get("account_id"),
                        errors=result["errors"]
                    )
                )

        # Prepare the response
        return UploadResponse(
            status="success",
            message="JSON file processed",
            total_processed=len(accounts_data),
            successful_count=len(successful_accounts),
            failed_count=len(failed_accounts),
            successful_accounts=successful_accounts,
            failed_accounts=failed_accounts
        )

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid JSON format: {str(e)}"
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing JSON file: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )

@router.post("/csv", response_model=UploadResponse)
async def upload_csv_file(file: UploadFile = File(...), current_user = Depends(get_current_active_user)):
    """
    Upload a CSV file containing account data

    The CSV file should have headers matching the required fields for account creation.
    Required columns: id, user.username, user.password, email.address, email.password,
    vault.address, vault.password, metadata.createdAt, metadata.sessionStart, metadata.guard

    Optional columns for steamguard: steamguard.deviceId, steamguard.shared_secret, etc.
    """
    # Validate file type
    if not file.filename.endswith('.csv'):
        logger.warning(f"Invalid file format: {file.filename}")
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a CSV file.")

    # Validate content type
    content_type = file.content_type
    if content_type not in ALLOWED_FILE_TYPES['csv']:
        logger.warning(f"Invalid content type: {content_type}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type: {content_type}. Allowed types: {', '.join(ALLOWED_FILE_TYPES['csv'])}"
        )

    try:
        # Read the file
        contents = await file.read()

        # Validate file size
        if len(contents) > MAX_FILE_SIZE:
            logger.warning(f"File too large: {len(contents)} bytes")
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024} MB"
            )

        # Parse CSV
        try:
            csv_text = contents.decode('utf-8')
            csv_file = io.StringIO(csv_text)
            csv_reader = csv.DictReader(csv_file)

            # Validate CSV headers
            required_headers = [
                'id', 'user.username', 'user.password', 'email.address', 'email.password',
                'vault.address', 'vault.password', 'metadata.createdAt', 'metadata.sessionStart', 'metadata.guard'
            ]

            headers = csv_reader.fieldnames
            if not headers:
                logger.error("CSV file has no headers")
                raise HTTPException(status_code=400, detail="CSV file has no headers")

            missing_headers = [header for header in required_headers if header not in headers]
            if missing_headers:
                logger.warning(f"Missing required CSV headers: {missing_headers}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required CSV headers: {', '.join(missing_headers)}"
                )
        except UnicodeDecodeError as e:
            logger.error(f"Error decoding CSV file: {e}")
            raise HTTPException(status_code=400, detail="Error decoding CSV file. Please ensure the file is UTF-8 encoded.")

        successful_accounts = []
        failed_accounts = []
        row_number = 0

        # Process each row in the CSV
        for row in csv_reader:
            row_number += 1

            # Validate row count
            if row_number > 1000:
                logger.warning(f"Too many rows in CSV file: {row_number}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Too many rows in CSV file. Maximum: 1000, got more than {row_number}"
                )

            # Convert CSV row to account data structure
            try:
                account_data = convert_csv_row_to_account_data(row)

                # Validate account data
                validation_result = validate_account_data(account_data)
                if not validation_result.valid:
                    logger.warning(f"Invalid account data in row {row_number}: {validation_result.errors}")
                    failed_accounts.append(
                        AccountValidationError(
                            account_id=account_data.get("id"),
                            row_number=row_number,
                            errors=[
                                ValidationErrorDetail(
                                    loc=error["field"].split("."),
                                    msg=error["message"],
                                    type="validation_error"
                                ) for error in validation_result.errors
                            ]
                        )
                    )
                    continue

                # Process valid account data
                result = process_account_data(account_data, row_number, current_user=current_user)

                if result["success"]:
                    successful_accounts.append(result["account_id"])
                else:
                    failed_accounts.append(
                        AccountValidationError(
                            account_id=result.get("account_id"),
                            row_number=row_number,
                            errors=result["errors"]
                        )
                    )
            except Exception as e:
                logger.error(f"Error processing CSV row {row_number}: {e}")
                logger.error(traceback.format_exc())

                failed_accounts.append(
                    AccountValidationError(
                        row_number=row_number,
                        errors=[
                            ValidationErrorDetail(
                                loc=["csv_row"],
                                msg=f"Error processing CSV row: {str(e)}",
                                type="csv_error"
                            )
                        ]
                    )
                )

        # Prepare the response
        return UploadResponse(
            status="success",
            message="CSV file processed",
            total_processed=row_number,
            successful_count=len(successful_accounts),
            failed_count=len(failed_accounts),
            successful_accounts=successful_accounts,
            failed_accounts=failed_accounts
        )

    except UnicodeDecodeError as e:
        logger.error(f"Error decoding CSV file: {e}")
        raise HTTPException(
            status_code=400,
            detail="Error decoding CSV file. Please ensure the file is UTF-8 encoded."
        )
    except csv.Error as e:
        logger.error(f"CSV parsing error: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"CSV parsing error: {str(e)}"
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing CSV file: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Error processing file: {str(e)}"
        )

def convert_csv_row_to_account_data(row: Dict[str, str]) -> Dict[str, Any]:
    """
    Convert a CSV row to the account data structure expected by the API

    Args:
        row: Dictionary representing a row from the CSV file

    Returns:
        Dictionary with the account data in the expected structure
    """
    # Initialize the account data structure
    account_data = {
        "id": row.get("id"),
        "user": {
            "username": row.get("user.username"),
            "password": row.get("user.password")
        },
        "vault": {
            "address": row.get("vault.address"),
            "password": row.get("vault.password")
        },
        "metadata": {
            "createdAt": int(row.get("metadata.createdAt", 0)),
            "sessionStart": int(row.get("metadata.sessionStart", 0)),
            "guard": row.get("metadata.guard", "")
        }
    }

    # Add email if provided
    if "email.address" in row and row["email.address"]:
        account_data["email"] = {
            "address": row.get("email.address"),
            "password": row.get("email.password", "")
        }

    # Add steamguard if any steamguard fields are provided
    steamguard_fields = {
        "deviceId": "steamguard.deviceId",
        "shared_secret": "steamguard.shared_secret",
        "serial_number": "steamguard.serial_number",
        "revocation_code": "steamguard.revocation_code",
        "uri": "steamguard.uri",
        "server_time": "steamguard.server_time",
        "account_name": "steamguard.account_name",
        "token_gid": "steamguard.token_gid",
        "identity_secret": "steamguard.identity_secret",
        "secret_1": "steamguard.secret_1",
        "status": "steamguard.status",
        "confirm_type": "steamguard.confirm_type"
    }

    # Check if any steamguard fields are present
    has_steamguard = any(field in row and row[field] for field in steamguard_fields.values())

    if has_steamguard:
        steamguard = {}
        for key, field in steamguard_fields.items():
            if field in row and row[field]:
                # Convert numeric fields
                if key in ["status", "confirm_type"]:
                    steamguard[key] = int(row[field])
                else:
                    steamguard[key] = row[field]

        # Only add steamguard if we have at least one field
        if steamguard:
            account_data["steamguard"] = steamguard

    return account_data
