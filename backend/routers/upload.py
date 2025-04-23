from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from fastapi.responses import JSONResponse
from dependencies import get_query_token
from db import conn
from typing import List, Dict, Any, Optional
import json
import csv
import io
from pydantic import BaseModel, Field, ValidationError
import traceback

# Import models from accounts router
from routers.accounts import User, Email, Vault, Metadata, Steamguard, ReceivedData

router = APIRouter(
    prefix="/upload",
    tags=["upload"],
    dependencies=[Depends(get_query_token)],
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

def process_account_data(account_data: Dict[Any, Any], row_number: Optional[int] = None) -> Dict[str, Any]:
    """
    Process and validate account data
    
    Args:
        account_data: Dictionary containing account data
        row_number: Row number in CSV file (if applicable)
        
    Returns:
        Dictionary with validation result
    """
    account_id = account_data.get("id", None)
    
    try:
        # Validate the data using Pydantic model
        validated_data = ReceivedData(**account_data)
        
        # Insert the account into the database
        cursor = conn.cursor()
        
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
                acc_uri
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
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
                accUri
            )
            
            cursor.execute(sql, params)
            result = cursor.fetchone()
            conn.commit()
            
            return {
                "success": True,
                "account_id": accId
            }
            
        except Exception as e:
            conn.rollback()
            print(f"Error creating account: {e}")
            
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
        print(f"Error processing account data: {e}")
        traceback.print_exc()
        
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
async def upload_json_file(file: UploadFile = File(...)):
    """
    Upload a JSON file containing account data
    
    The JSON file should contain an array of account objects or a single account object.
    Each account object should follow the structure defined in the ReceivedData model.
    """
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a JSON file.")
    
    try:
        # Read and parse the JSON file
        contents = await file.read()
        json_data = json.loads(contents.decode('utf-8'))
        
        # Handle both single account and array of accounts
        accounts_data = json_data if isinstance(json_data, list) else [json_data]
        
        successful_accounts = []
        failed_accounts = []
        
        # Process each account
        for account_data in accounts_data:
            result = process_account_data(account_data)
            
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
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        print(f"Error processing JSON file: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@router.post("/csv", response_model=UploadResponse)
async def upload_csv_file(file: UploadFile = File(...)):
    """
    Upload a CSV file containing account data
    
    The CSV file should have headers matching the required fields for account creation.
    Required columns: id, user.username, user.password, email.address, email.password,
    vault.address, vault.password, metadata.createdAt, metadata.sessionStart, metadata.guard
    
    Optional columns for steamguard: steamguard.deviceId, steamguard.shared_secret, etc.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file format. Please upload a CSV file.")
    
    try:
        # Read and parse the CSV file
        contents = await file.read()
        csv_file = io.StringIO(contents.decode('utf-8'))
        csv_reader = csv.DictReader(csv_file)
        
        successful_accounts = []
        failed_accounts = []
        row_number = 0
        
        # Process each row in the CSV
        for row in csv_reader:
            row_number += 1
            
            # Convert CSV row to account data structure
            try:
                account_data = convert_csv_row_to_account_data(row)
                result = process_account_data(account_data, row_number)
                
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
                print(f"Error processing CSV row {row_number}: {e}")
                traceback.print_exc()
                
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
        
    except Exception as e:
        print(f"Error processing CSV file: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

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
