from fastapi import APIRouter, Depends, HTTPException
from dependencies import get_query_token
from db import get_user_db_connection
from typing import List, Optional
from pydantic import BaseModel
from routers.auth import get_current_active_user

router = APIRouter(
    prefix="/account-status",
    tags=["account-status"],
    # Remove the dependency on get_query_token as we're using JWT authentication
    # dependencies=[Depends(get_query_token)],
    responses={404: {"description": "Not found"}},
)

class AccountStatusUpdate(BaseModel):
    acc_id: str
    status: bool

class BulkStatusUpdate(BaseModel):
    account_ids: List[str]
    status: bool

@router.post("/lock")
async def lock_account(acc_id: str, status: bool, current_user = Depends(get_current_active_user)):
    """Lock or unlock an account"""
    # Use user-specific database connection with RLS
    with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as user_conn:
        cursor = user_conn.cursor()

        try:
            cursor.execute("UPDATE accounts SET lock = %s WHERE acc_id = %s RETURNING acc_id", (status, acc_id))
            result = cursor.fetchone()
            user_conn.commit()

            if not result:
                raise HTTPException(status_code=404, detail="Account not found or you don't have permission to update it")

            return {"acc_id": acc_id, "lock": status, "success": True}
        except Exception as e:
            user_conn.rollback()
            print(f"Error updating account lock status: {e}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail="Error updating account lock status")
        finally:
            cursor.close()

@router.post("/lock/bulk")
async def lock_accounts_bulk(update: BulkStatusUpdate, current_user = Depends(get_current_active_user)):
    """Lock or unlock multiple accounts at once"""
    # Use user-specific database connection with RLS
    with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as user_conn:
        cursor = user_conn.cursor()

        try:
            # Convert list to tuple for SQL IN clause
            acc_ids_tuple = tuple(update.account_ids)

            if len(acc_ids_tuple) == 1:
                # Special case for single item (needs trailing comma)
                cursor.execute(
                    "UPDATE accounts SET lock = %s WHERE acc_id IN (%s) RETURNING acc_id",
                    (update.status, acc_ids_tuple[0])
                )
            else:
                cursor.execute(
                    f"UPDATE accounts SET lock = %s WHERE acc_id IN %s RETURNING acc_id",
                    (update.status, acc_ids_tuple)
                )

            updated_ids = [row[0] for row in cursor.fetchall()]
            user_conn.commit()

            return {
                "updated_count": len(updated_ids),
                "updated_ids": updated_ids,
                "lock": update.status,
                "success": True
            }
        except Exception as e:
            user_conn.rollback()
            print(f"Error updating bulk account lock status: {e}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail="Error updating account lock status")
        finally:
            cursor.close()

@router.post("/prime")
async def set_prime_status(acc_id: str, status: bool, current_user = Depends(get_current_active_user)):
    """Set the prime status of an account"""
    # Use user-specific database connection with RLS
    with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as user_conn:
        cursor = user_conn.cursor()

        try:
            cursor.execute("UPDATE accounts SET prime = %s WHERE acc_id = %s RETURNING acc_id", (status, acc_id))
            result = cursor.fetchone()
            user_conn.commit()

            if not result:
                raise HTTPException(status_code=404, detail="Account not found or you don't have permission to update it")

            return {"acc_id": acc_id, "prime": status, "success": True}
        except Exception as e:
            user_conn.rollback()
            print(f"Error updating account prime status: {e}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail="Error updating account prime status")
        finally:
            cursor.close()

@router.post("/prime/bulk")
async def set_prime_status_bulk(update: BulkStatusUpdate, current_user = Depends(get_current_active_user)):
    """Set the prime status of multiple accounts at once"""
    # Use user-specific database connection with RLS
    with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as user_conn:
        cursor = user_conn.cursor()

        try:
            # Convert list to tuple for SQL IN clause
            acc_ids_tuple = tuple(update.account_ids)

            if len(acc_ids_tuple) == 1:
                # Special case for single item (needs trailing comma)
                cursor.execute(
                    "UPDATE accounts SET prime = %s WHERE acc_id IN (%s) RETURNING acc_id",
                    (update.status, acc_ids_tuple[0])
                )
            else:
                cursor.execute(
                    f"UPDATE accounts SET prime = %s WHERE acc_id IN %s RETURNING acc_id",
                    (update.status, acc_ids_tuple)
                )

            updated_ids = [row[0] for row in cursor.fetchall()]
            user_conn.commit()

            return {
                "updated_count": len(updated_ids),
                "updated_ids": updated_ids,
                "prime": update.status,
                "success": True
            }
        except Exception as e:
            user_conn.rollback()
            print(f"Error updating bulk account prime status: {e}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail="Error updating account prime status")
        finally:
            cursor.close()

@router.get("/fresh")
async def get_fresh_account(limit: int = 1, lock: bool = False, current_user = Depends(get_current_active_user)):
    """Get fresh (unused) accounts and optionally lock them"""
    # Use user-specific database connection with RLS
    with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as user_conn:
        cursor = user_conn.cursor()

        try:
            cursor.execute("""
                SELECT acc_id, acc_username
                FROM accounts
                WHERE prime = false AND lock = false AND perm_lock = false
                ORDER BY id ASC
                LIMIT %s
            """, (limit,))

            results = cursor.fetchall()

            if not results:
                return {"accounts": [], "count": 0}

            accounts = []
            for row in results:
                accounts.append({"acc_id": row[0], "acc_username": row[1]})

                # If lock is requested, lock each account
                if lock:
                    cursor.execute("UPDATE accounts SET lock = true WHERE acc_id = %s", (row[0],))

            if lock:
                user_conn.commit()

            return {"accounts": accounts, "count": len(accounts)}
        except Exception as e:
            if lock:
                user_conn.rollback()
            print(f"Error retrieving fresh accounts: {e}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail="Error retrieving fresh accounts")
        finally:
            cursor.close()
