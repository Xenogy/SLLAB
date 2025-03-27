from fastapi import Depends, FastAPI

from .dependencies import get_query_token, get_token_header
from .routers import accounts, cards

app = FastAPI()


app.include_router(accounts.router)
app.include_router(cards.router)

@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}
