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

router = APIRouter(
    prefix="/cards",
    tags=["cards"],
    dependencies=[Depends(get_query_token)],
    responses={404: {"description": "Not found"}},
)

@router.get('available')
async def get_available():
    cursor = conn.cursor()
    passed = False
    pack = None

    while passed == False:
        try:
            cursor.execute("SELECT id,code1,code2 FROM cards WHERE redeemed = false")
            result = cursor.fetchone()
            cursor.close()
            try_pack = {'id': result[0], 'code1': result[1], 'code2': result[2] or None}
            
            passed = True
            pack = try_pack
        except(err):
            print(err)
            time.sleep(3)

    return pack

@router.post('/')
async def new_cards(cardList: list[list[str]]):
    cursor = conn.cursor()

    for cardPack in cardList:
        if len(cardPack) > 1:
            cursor.execute("INSERT INTO cards(code1,code2) VALUES(%s,%s)", (cardPack[0],cardPack[1]))
        else:
            cursor.execute("INSERT INTO cards(code1) VALUES(%s)", (cardPack[0],))
    conn.commit()
    cursor.close()

    return True

@router.post('/redeem')
async def redeem_card(id: int = 0, codeSearch: str = ""):
    assert (id != 0 or codeSearch != "") == True, "No card_id or code_search supplied"
    cursor = conn.cursor()
    if id != 0:
        cursor.execute("UPDATE cards SET redeemed=true WHERE id = %s", (id,))

    if codeSearch != "":
        cursor.execute("UPDATE cards SET redeemed=true WHERE code1 = %s OR code2 = %s", (codeSearch,codeSearch))

    conn.commit()
    cursor.close()

    return True
