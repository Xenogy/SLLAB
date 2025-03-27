from fastapi import APIRouter, Request, Depends, HTTPException
from ..dependencies import get_query_token
import psycopg2
from pydantic import BaseModel
from typing import List
import time
import hmac
import json
import struct
import base64
import requests
from hashlib import sha1
import platform
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
    tags: List  # You could also be more specific if you know the type of items in the list.
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
    email: Email
    vault: Vault
    metadata: Metadata
    steamguard: Steamguard = None

router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
    dependencies=[Depends(get_query_token)],
    responses={404: {"description": "Not found"}},
)

def getQueryTime():
    try:
        request = requests.post('https://api.steampowered.com/ITwoFactorService/QueryTime/v0001', timeout=30)
        json_data = request.json()
        server_time = int(json_data['response']['server_time']) - time.time()
        return server_time
    except:
        return 0

symbols = '23456789BCDFGHJKMNPQRTVWXY'
def getGuardCode(shared_secret):
    code = ''
    timestamp = time.time() + getQueryTime()
    _hmac = hmac.new(base64.b64decode(shared_secret), struct.pack('>Q', int(timestamp/30)), sha1).digest()
    _ord = ord(_hmac[19:20]) & 0xF
    value = struct.unpack('>I', _hmac[_ord:_ord+4])[0] & 0x7fffffff
    for i in range(5):
        code += symbols[value % len(symbols)]
        value = int(value / len(symbols))
    return code

@router.get("/")
async def get_accounts(limit: int = 10):
    return "balls"

@router.get("/{username}")
async def get_username(username: str = "", steamid: str = ""):
    return [username, steamid]

@router.get("/auth/2fa")
async def get_auth_code(acc_id: str):
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT acc_shared_secret AS secret FROM accounts WHERE acc_id = %s", (acc_id,))
        query = cursor.fetchone()[0]
    except(err):
        print(err)
        cursor.close()
        return False

    cursor.close()
    code = getGuardCode(query)
    
    return code

@router.post("/info")
async def get_account_info(acc_id: str, datatype: str):
    cursor = conn.cursor()
    cursor.execute(f"SELECT {datatype} AS data FROM accounts WHERE acc_id = %s", (acc_id,))
    query = cursor.fetchone()[0]
    cursor.close()

    return query

@router.post("/lock")
async def lock_account(status: bool, acc_id):
    cursor = conn.cursor()

    failed = False
    try:
        cursor.execute("UPDATE accounts SET lock = %s WHERE acc_id = %s", (status, acc_id))
        conn.commit()
    except(err):
        print(err)
        failed = True

    cursor.close()
    return failed == False

@router.post("/primed")
async def set_prime_status(status: bool, acclist: list[str] = ['acc_id'], accid: str = None):
    cursor = conn.cursor()
    print(acclist)
    assert (acclist != ['acc_id'] or accid != None) == True, "no acclist or accid supplied" 
    def setPrime(acc_id):
        cursor.execute(f"""
        UPDATE accounts
            SET prime=%s
            WHERE acc_id = %s;""", (status,acc_id))
        print(f'Set {acc_id} prime status to {status}')

    try:
        if acclist != ['acc_id']:
            for acc_id in acclist:
                setPrime(acc_id)
        elif accid != None:
            setPrime(accid)

        conn.commit()
    except(err):
        print(err)
    cursor.close()

    return True

@router.get("/fresh/")
async def get_fresh_account(limit: int = 1, lock: bool = False):
    cursor = conn.cursor()
    fetched_acc = False
    try:
        cursor.execute("SELECT acc_id as acc_id,acc_username as acc_username FROM accounts WHERE prime = false AND lock = false AND perm_lock = false ORDER BY id ASC LIMIT %s", (limit,))
        fetched_acc = cursor.fetchone()[0]
        
        if lock == True:
            cursor.execute("UPDATE accounts SET lock = %s WHERE acc_id = %s", (lock, fetched_acc))
            conn.commit()
    except(err):
        print(err)

    cursor.close()

    return fetched_acc

@router.post("/new")
async def new_account(request: Request, debug: bool = False):
    accObject = await request.json()

    accId = accObject["id"]

    accUser = accObject["user"]
    accUsername = accUser["username"]
    accPassword = accUser["password"]

    accEmail = accObject["email"]
    accEmailAddress = accEmail["address"]
    accEmailPassword = accEmail["password"]

    accVault = accObject["vault"]
    accVaultAddress = accVault["address"]
    accVaultPassword = accVault["password"]

    accMetadata = accObject["metadata"]
    accCreatedAt = accMetadata["createdAt"]
    accSessionStart = accMetadata["sessionStart"]
    
    accSteamguard = None
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
    if debug == True: 
        print(f"Debug:\n{accObject}")
        return True
    if accEmailAddress.find("@demoemail.com") >= 0:
        print(f'Received test webhook with account object:\n{accObject}')
        return True
    
    print(accObject)
    if "steamguard" in accObject.keys():
        accSteamguard = accObject["steamguard"]
        accSteamguardAccountName = accSteamguard["account_name"]
        accConfirmType = accSteamguard["confirm_type"]
        accDeviceId = accSteamguard["deviceId"]
        accIdentitySecret = accSteamguard["identity_secret"]
        accRevocationCode = accSteamguard["revocation_code"]
        accSecret1 = accSteamguard["secret_1"]
        accSerialNumber = accSteamguard["serial_number"]
        accServerTime = accSteamguard["server_time"]
        accSharedSecret = accSteamguard["shared_secret"]
        accStatus = accSteamguard["status"]
        accTokenGid = accSteamguard["token_gid"]
        accUri = accSteamguard["uri"]
    print(f'Received new account: ({accUsername} : {accEmailAddress})') 
    # Assuming you already have a psycopg2 connection and cursor established:
    cursor = conn.cursor()

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
    ON CONFLICT (acc_id) DO NOTHING;
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
    conn.commit()
    cursor.close()
 
@router.post("/new/man")
async def new_manual_account(accList: list[ReceivedData], debug: bool = False):
    for accObject in accList:
        accId = accObject.id

        accUser = accObject.user
        accUsername = accUser.username
        accPassword = accUser.password

        accEmail = accObject.email
        accEmailAddress = accEmail.address
        accEmailPassword = accEmail.password

        accVault = accObject.vault
        accVaultAddress = accVault.address
        accVaultPassword = accVault.password

        accMetadata = accObject.metadata
        accCreatedAt = accMetadata.createdAt
        accSessionStart = accMetadata.sessionStart
    
        accSteamguard = None
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

        print(accObject.steamguard)
        if accObject.steamguard != None:
            accSteamguard = accObject.steamguard
            accSteamguardAccountName = accSteamguard.account_name
            accConfirmType = accSteamguard.confirm_type
            accDeviceId = accSteamguard.deviceId
            accIdentitySecret = accSteamguard.identity_secret
            accRevocationCode = accSteamguard.revocation_code
            accSecret1 = accSteamguard.secret_1
            accSerialNumber = accSteamguard.serial_number
            accServerTime = accSteamguard.server_time
            accSharedSecret = accSteamguard.shared_secret
            accStatus = accSteamguard.status
            accTokenGid = accSteamguard.token_gid
            accUri = accSteamguard.uri

        if debug == True: 
            print(f"Debug:\n{accObject}")
            continue
        if accEmailAddress.find("@demoemail.com") >= 0:
            print(f'Received test webhook with account object:\n{accObject}')
            continue
    
        print(f'Received new account: ({accUsername} : {accEmailAddress})') 
        # Assuming you already have a psycopg2 connection and cursor established:
        cursor = conn.cursor()

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
        ON CONFLICT (acc_id) DO NOTHING;
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
    if debug == True:
        return True
    conn.commit()
    cursor.close()
