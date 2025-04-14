import os
from typing import Annotated
from fastapi import Header, HTTPException

async def get_token_header(x_token: Annotated[str, Header()]):
    if x_token != os.environ['X_TOKEN']:
        raise HTTPException(status_code=400, detail="unauthorized")


async def get_query_token(token: str):
    if token != os.environ['API_TOKEN']:
        raise HTTPException(status_code=400, detail="unauthorized")
