from fastapi import APIRouter, Request, Depends, HTTPException
from ..dependencies import get_query_token
import psycopg2
from pydantic import BaseModel, Field
from typing import List, Optional
import time
import uuid
from dotenv import load_dotenv
import os

env_path = os.path.join(os.path.dirname(__file__), '/../.env')
load_dotenv(dotenv_path=env_path)

db_host = os.getenv('PG_HOST')
db_port = os.getenv('PG_PORT')
db_user = os.getenv('PG_USER')
db_pass = os.getenv('PG_PASSWORD')
time.sleep(5)
conn = psycopg2.connect(f"host={db_host} port=5432 dbname=accountdb user={db_user} password={db_pass} target_session_attrs=read-write")

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
    dependencies=[Depends(get_query_token)],
    responses={404: {"description": "Not found"}},
)

@router.get("/{acc_id}", response_model=List[HardwareResponse])
async def get_hardware_by_account(acc_id: str, vm_id: int):
    """Get hardware information for a specific account"""
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, acc_id, bios_vendor, bios_version, disk_serial, disk_model,
                   smbios_uuid, mb_manufacturer, mb_product, mb_version, mb_serial,
                   mac_address, vmid, pcname, machine_guid, hwprofile_guid
            FROM hardware
            WHERE acc_id = %s
        """, (acc_id,))

        results = cursor.fetchall()
        cursor.close()

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
        cursor.close()
        raise HTTPException(status_code=500, detail="Error retrieving hardware information")

@router.post("/", response_model=HardwareResponse)
async def create_hardware(hardware: HardwareCreate):
    """Add new hardware information"""
    cursor = conn.cursor()

    try:
        sql = """
        INSERT INTO hardware (
            acc_id, bios_vendor, bios_version, disk_serial, disk_model,
            smbios_uuid, mb_manufacturer, mb_product, mb_version, mb_serial,
            mac_address, vmid, pcname, machine_guid, hwprofile_guid
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
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
            hardware.hwprofile_guid
        )

        cursor.execute(sql, params)
        hardware_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()

        # Return the created hardware with its ID
        return {**hardware.dict(), "id": hardware_id}

    except Exception as e:
        conn.rollback()
        print(f"Error creating hardware: {e}")
        cursor.close()
        raise HTTPException(status_code=500, detail="Error creating hardware information")

@router.put("/{hardware_id}", response_model=HardwareResponse)
async def update_hardware(hardware_id: int, hardware: HardwareBase):
    """Update hardware information"""
    cursor = conn.cursor()

    try:
        # First check if the hardware exists
        cursor.execute("SELECT id FROM hardware WHERE id = %s", (hardware_id,))
        result = cursor.fetchone()

        if not result:
            cursor.close()
            raise HTTPException(status_code=404, detail="Hardware not found")

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
        conn.commit()
        cursor.close()

        # Return the updated hardware
        return {**hardware.dict(), "id": hardware_id}

    except Exception as e:
        conn.rollback()
        print(f"Error updating hardware: {e}")
        cursor.close()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Error updating hardware information")

@router.delete("/{hardware_id}")
async def delete_hardware(hardware_id: int):
    """Delete hardware information"""
    cursor = conn.cursor()

    try:
        # First check if the hardware exists
        cursor.execute("SELECT id FROM hardware WHERE id = %s", (hardware_id,))
        result = cursor.fetchone()

        if not result:
            cursor.close()
            raise HTTPException(status_code=404, detail="Hardware not found")

        cursor.execute("DELETE FROM hardware WHERE id = %s", (hardware_id,))
        conn.commit()
        cursor.close()

        return {"message": "Hardware deleted successfully"}

    except Exception as e:
        conn.rollback()
        print(f"Error deleting hardware: {e}")
        cursor.close()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Error deleting hardware information")

@router.get("/search/mac/{mac_address}", response_model=List[HardwareResponse])
async def search_by_mac_address(mac_address: str):
    """Search hardware by MAC address"""
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, acc_id, bios_vendor, bios_version, disk_serial, disk_model,
                   smbios_uuid, mb_manufacturer, mb_product, mb_version, mb_serial,
                   mac_address, vmid, pcname, machine_guid, hwprofile_guid
            FROM hardware
            WHERE mac_address = %s
        """, (mac_address,))

        results = cursor.fetchall()
        cursor.close()

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
        print(f"Error searching hardware by MAC: {e}")
        cursor.close()
        raise HTTPException(status_code=500, detail="Error searching hardware information")

@router.get("/search/uuid/{smbios_uuid}", response_model=List[HardwareResponse])
async def search_by_smbios_uuid(smbios_uuid: uuid.UUID):
    """Search hardware by SMBIOS UUID"""
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, acc_id, bios_vendor, bios_version, disk_serial, disk_model,
                   smbios_uuid, mb_manufacturer, mb_product, mb_version, mb_serial,
                   mac_address, vmid, pcname, machine_guid, hwprofile_guid
            FROM hardware
            WHERE smbios_uuid = %s
        """, (str(smbios_uuid),))

        results = cursor.fetchall()
        cursor.close()

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
        print(f"Error searching hardware by UUID: {e}")
        cursor.close()
        raise HTTPException(status_code=500, detail="Error searching hardware information")

@router.post("/bulk", response_model=List[HardwareResponse])
async def create_hardware_bulk(hardware_list: List[HardwareCreate]):
    """Add multiple hardware entries at once"""
    cursor = conn.cursor()

    try:
        created_hardware = []

        for hardware in hardware_list:
            sql = """
            INSERT INTO hardware (
                acc_id, bios_vendor, bios_version, disk_serial, disk_model,
                smbios_uuid, mb_manufacturer, mb_product, mb_version, mb_serial,
                mac_address, vmid, pcname, machine_guid, hwprofile_guid
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
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
                hardware.hwprofile_guid
            )

            cursor.execute(sql, params)
            hardware_id = cursor.fetchone()[0]
            created_hardware.append({**hardware.dict(), "id": hardware_id})

        conn.commit()
        cursor.close()

        return created_hardware

    except Exception as e:
        conn.rollback()
        print(f"Error creating bulk hardware: {e}")
        cursor.close()
        raise HTTPException(status_code=500, detail="Error creating hardware information")