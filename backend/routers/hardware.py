from fastapi import APIRouter, Request, Depends, HTTPException, Path
from dependencies import get_query_token
import psycopg2
from psycopg2 import sql
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import time
import uuid
from db import get_user_db_connection
from dotenv import load_dotenv
import os
from routers.auth import get_current_active_user

# Load environment variables if needed for other settings
env_path = os.path.join(os.path.dirname(__file__), '/../.env')
load_dotenv(dotenv_path=env_path)

class HardwareBase(BaseModel):
    acc_id: str
    bios_vendor: Optional[str] = None
    bios_version: Optional[str] = None
    disk_serial: Optional[str] = None
    disk_model: Optional[str] = None
    smbios_uuid: Optional[uuid.UUID] = None
    mb_manufacturer: Optional[str] = None
    mb_product: Optional[str] = None
    mb_version: Optional[str] = None
    mb_serial: Optional[str] = None
    mac_address: Optional[str] = None
    vmid: Optional[int] = None
    pcname: Optional[str] = None
    machine_guid: Optional[uuid.UUID] = None
    hwprofile_guid: Optional[uuid.UUID] = None

class HardwareCreate(HardwareBase):
    pass

class HardwareResponse(HardwareBase):
    id: int

router = APIRouter(
    prefix="/hardware",
    tags=["hardware"],
    # Remove the dependency on get_query_token as we're using JWT authentication
    # dependencies=[Depends(get_query_token)],
    responses={404: {"description": "Not found"}},
)

def get_hardware(searchType: str, searchValue: str, current_user: dict) -> List[Dict[str, Any]]:
    """
    Generic function to search hardware by any column

    Args:
        searchType: The column to search in
        searchValue: The value to search for
        current_user: The current authenticated user

    Returns:
        List of hardware entries matching the search criteria
    """
    ALLOWED_SEARCH_COLUMNS = [
        "acc_id", "bios_vendor", "bios_version", "disk_serial", "disk_model",
        "smbios_uuid", "mb_manufacturer", "mb_product", "mb_version", "mb_serial",
        "mac_address", "vmid", "pcname", "machine_guid", "hwprofile_guid"
    ]

    # Input validation
    if searchType not in ALLOWED_SEARCH_COLUMNS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid search type. Allowed types: {', '.join(ALLOWED_SEARCH_COLUMNS)}"
        )

    # Use user-specific database connection with RLS
    with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as user_conn:
        cursor = user_conn.cursor()

        try:
            # Safely construct SQL using psycopg2.sql
            query = sql.SQL("""
                SELECT id, acc_id, bios_vendor, bios_version, disk_serial, disk_model,
                       smbios_uuid, mb_manufacturer, mb_product, mb_version, mb_serial,
                       mac_address, vmid, pcname, machine_guid, hwprofile_guid
                FROM {table}
                WHERE {column} = %s
            """).format(
                table=sql.Identifier('hardware'),      # Safely quote table name
                column=sql.Identifier(searchType)       # Safely quote column name (validated above)
            )

            # Execute with parameterization
            print(f"Executing query with {searchType}={searchValue}")
            cursor.execute(query, (searchValue,))

            results = cursor.fetchall()
            if not results:
                return []

            hardware_list = []
            for row in results:
                hardware = {
                    "id": row[0],
                    "acc_id": row[1],
                    "bios_vendor": row[2],
                    "bios_version": row[3],
                    "disk_serial": row[4],
                    "disk_model": row[5],
                    "smbios_uuid": row[6],
                    "mb_manufacturer": row[7],
                    "mb_product": row[8],
                    "mb_version": row[9],
                    "mb_serial": row[10],
                    "mac_address": row[11],
                    "vmid": row[12],
                    "pcname": row[13],
                    "machine_guid": row[14],
                    "hwprofile_guid": row[15]
                }
                hardware_list.append(hardware)

            return hardware_list

        except Exception as e:
            print(f"Error retrieving hardware: {e}")
            raise HTTPException(status_code=500, detail=f"Error retrieving hardware information: {str(e)}")
        finally:
            cursor.close()

@router.get("/search/mac/{mac_address}", response_model=List[HardwareResponse])
async def search_by_mac_address(mac_address: str, current_user = Depends(get_current_active_user)):
    """Search hardware by MAC address"""
    return get_hardware('mac_address', mac_address, current_user)

@router.get("/search/uuid/{smbios_uuid}", response_model=List[HardwareResponse])
async def search_by_smbios_uuid(smbios_uuid: str, current_user = Depends(get_current_active_user)):
    """Search hardware by SMBIOS UUID"""
    return get_hardware('smbios_uuid', smbios_uuid, current_user)

@router.get("/search/{searchType}/{searchValue}", response_model=List[HardwareResponse])
async def search_hardware(searchType: str, searchValue: str, current_user = Depends(get_current_active_user)):
    """Search hardware by a specific field"""
    return get_hardware(searchType, searchValue, current_user)

@router.get("/{acc_id}", response_model=List[HardwareResponse])
async def get_hardware_by_account(acc_id: str, current_user = Depends(get_current_active_user)):
    """Get hardware information for a specific account"""
    return get_hardware('acc_id', acc_id, current_user)

@router.post("/", response_model=HardwareResponse)
async def create_hardware(hardware: HardwareCreate, current_user = Depends(get_current_active_user)):
    """Add new hardware information"""
    # Use user-specific database connection with RLS
    with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as user_conn:
        cursor = user_conn.cursor()

        try:
            sql = """
            INSERT INTO hardware (
                acc_id, bios_vendor, bios_version, disk_serial, disk_model,
                smbios_uuid, mb_manufacturer, mb_product, mb_version, mb_serial,
                mac_address, vmid, pcname, machine_guid, hwprofile_guid, owner_id
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            ) RETURNING id
            """

            params = (
                hardware.acc_id,
                hardware.bios_vendor,
                hardware.bios_version,
                hardware.disk_serial,
                hardware.disk_model,
                hardware.smbios_uuid,
                hardware.mb_manufacturer,
                hardware.mb_product,
                hardware.mb_version,
                hardware.mb_serial,
                hardware.mac_address,
                hardware.vmid,
                hardware.pcname,
                hardware.machine_guid,
                hardware.hwprofile_guid,
                current_user["id"]  # Set the owner_id to the current user's ID
            )

            cursor.execute(sql, params)
            hardware_id = cursor.fetchone()[0]
            user_conn.commit()

            # Return the created hardware with its ID
            return {**hardware.dict(), "id": hardware_id}

        except Exception as e:
            user_conn.rollback()
            print(f"Error creating hardware: {e}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail="Error creating hardware information")
        finally:
            cursor.close()

@router.put("/{hardware_id}", response_model=HardwareResponse)
async def update_hardware(hardware_id: int, hardware: HardwareBase, current_user = Depends(get_current_active_user)):
    """Update hardware information"""
    # Use user-specific database connection with RLS
    with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as user_conn:
        cursor = user_conn.cursor()

        try:
            # First check if the hardware exists and belongs to the current user (RLS will handle this)
            cursor.execute("SELECT id FROM hardware WHERE id = %s", (hardware_id,))
            result = cursor.fetchone()

            if not result:
                raise HTTPException(status_code=404, detail="Hardware not found or you don't have permission to update it")

            sql = """
            UPDATE hardware SET
                acc_id = %s,
                bios_vendor = %s,
                bios_version = %s,
                disk_serial = %s,
                disk_model = %s,
                smbios_uuid = %s,
                mb_manufacturer = %s,
                mb_product = %s,
                mb_version = %s,
                mb_serial = %s,
                mac_address = %s,
                vmid = %s,
                pcname = %s,
                machine_guid = %s,
                hwprofile_guid = %s
            WHERE id = %s
            RETURNING id
            """

            params = (
                hardware.acc_id,
                hardware.bios_vendor,
                hardware.bios_version,
                hardware.disk_serial,
                hardware.disk_model,
                hardware.smbios_uuid,
                hardware.mb_manufacturer,
                hardware.mb_product,
                hardware.mb_version,
                hardware.mb_serial,
                hardware.mac_address,
                hardware.vmid,
                hardware.pcname,
                hardware.machine_guid,
                hardware.hwprofile_guid,
                hardware_id
            )

            cursor.execute(sql, params)
            user_conn.commit()

            # Return the updated hardware
            return {**hardware.dict(), "id": hardware_id}

        except Exception as e:
            user_conn.rollback()
            print(f"Error updating hardware: {e}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail="Error updating hardware information")
        finally:
            cursor.close()

@router.delete("/{hardware_id}")
async def delete_hardware(hardware_id: int, current_user = Depends(get_current_active_user)):
    """Delete hardware information"""
    # Use user-specific database connection with RLS
    with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as user_conn:
        cursor = user_conn.cursor()

        try:
            # First check if the hardware exists and belongs to the current user (RLS will handle this)
            cursor.execute("SELECT id FROM hardware WHERE id = %s", (hardware_id,))
            result = cursor.fetchone()

            if not result:
                raise HTTPException(status_code=404, detail="Hardware not found or you don't have permission to delete it")

            cursor.execute("DELETE FROM hardware WHERE id = %s", (hardware_id,))
            user_conn.commit()

            return {"message": "Hardware deleted successfully"}

        except Exception as e:
            user_conn.rollback()
            print(f"Error deleting hardware: {e}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail="Error deleting hardware information")
        finally:
            cursor.close()

@router.post("/bulk", response_model=List[HardwareResponse])
async def create_hardware_bulk(hardware_list: List[HardwareCreate], current_user = Depends(get_current_active_user)):
    """Add multiple hardware entries at once"""
    # Use user-specific database connection with RLS
    with get_user_db_connection(user_id=current_user["id"], user_role=current_user["role"]) as user_conn:
        cursor = user_conn.cursor()

        try:
            created_hardware = []

            for hardware in hardware_list:
                sql = """
                INSERT INTO hardware (
                    acc_id, bios_vendor, bios_version, disk_serial, disk_model,
                    smbios_uuid, mb_manufacturer, mb_product, mb_version, mb_serial,
                    mac_address, vmid, pcname, machine_guid, hwprofile_guid, owner_id
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
                """

                params = (
                    hardware.acc_id,
                    hardware.bios_vendor,
                    hardware.bios_version,
                    hardware.disk_serial,
                    hardware.disk_model,
                    hardware.smbios_uuid,
                    hardware.mb_manufacturer,
                    hardware.mb_product,
                    hardware.mb_version,
                    hardware.mb_serial,
                    hardware.mac_address,
                    hardware.vmid,
                    hardware.pcname,
                    hardware.machine_guid,
                    hardware.hwprofile_guid,
                    current_user["id"]  # Set the owner_id to the current user's ID
                )

                cursor.execute(sql, params)
                hardware_id = cursor.fetchone()[0]
                created_hardware.append({**hardware.dict(), "id": hardware_id})

            user_conn.commit()
            return created_hardware

        except Exception as e:
            user_conn.rollback()
            print(f"Error creating bulk hardware: {e}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail="Error creating hardware information")
        finally:
            cursor.close()
