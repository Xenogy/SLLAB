from fastapi import APIRouter, Depends, HTTPException
from ..dependencies import get_query_token
from ..db import conn
import time
import hmac
import struct
import base64
import requests
from hashlib import sha1
from typing import Optional

router = APIRouter(
    prefix="/steam",
    tags=["steam"],
    dependencies=[Depends(get_query_token)],
    responses={404: {"description": "Not found"}},
)

def get_query_time():
    """Get the time difference between local time and Steam server time"""
    try:
        request = requests.post('https://api.steampowered.com/ITwoFactorService/QueryTime/v0001', timeout=30)
        json_data = request.json()
        server_time = int(json_data['response']['server_time']) - time.time()
        return server_time
    except:
        return 0

symbols = '23456789BCDFGHJKMNPQRTVWXY'
def get_guard_code(shared_secret):
    """Generate a Steam Guard code from a shared secret"""
    code = ''
    timestamp = time.time() + get_query_time()
    _hmac = hmac.new(base64.b64decode(shared_secret), struct.pack('>Q', int(timestamp/30)), sha1).digest()
    _ord = ord(_hmac[19:20]) & 0xF
    value = struct.unpack('>I', _hmac[_ord:_ord+4])[0] & 0x7fffffff
    for i in range(5):
        code += symbols[value % len(symbols)]
        value = int(value / len(symbols))
    return code

@router.get("/auth/2fa")
async def get_auth_code(acc_id: str):
    """Generate a Steam Guard 2FA code for a specific account"""
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT acc_shared_secret AS secret FROM accounts WHERE acc_id = %s", (acc_id,))
        result = cursor.fetchone()
        if not result:
            cursor.close()
            raise HTTPException(status_code=404, detail="Account not found")
        
        shared_secret = result[0]
    except Exception as e:
        print(f"Error retrieving shared secret: {e}")
        cursor.close()
        raise HTTPException(status_code=500, detail="Error retrieving authentication data")

    cursor.close()
    code = get_guard_code(shared_secret)
    
    return {"acc_id": acc_id, "auth_code": code}

@router.get("/auth/info")
async def get_steam_auth_info(acc_id: str):
    """Get Steam authentication information for an account"""
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                acc_steamguard_account_name, 
                acc_device_id, 
                acc_shared_secret,
                acc_identity_secret,
                acc_confirm_type
            FROM accounts 
            WHERE acc_id = %s
        """, (acc_id,))
        
        result = cursor.fetchone()
        if not result:
            cursor.close()
            raise HTTPException(status_code=404, detail="Account not found")
        
        auth_info = {
            "account_name": result[0],
            "device_id": result[1],
            "shared_secret": result[2],
            "identity_secret": result[3],
            "confirm_type": result[4]
        }
    except Exception as e:
        print(f"Error retrieving Steam auth info: {e}")
        cursor.close()
        raise HTTPException(status_code=500, detail="Error retrieving authentication data")

    cursor.close()
    return auth_info
