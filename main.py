from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .dependencies import get_query_token, get_token_header
from .routers import accounts, cards, hardware, steam_auth, account_status

app = FastAPI(
    title="Account Management API",
    description="API for managing accounts, hardware, and authentication",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(accounts.router)
app.include_router(cards.router)
app.include_router(hardware.router)
app.include_router(steam_auth.router)
app.include_router(account_status.router)

@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}
