import os
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Use absolute imports instead of relative imports
from dependencies import get_query_token, get_token_header
from routers import accounts, cards, hardware, steam_auth, account_status, auth

app = FastAPI(
    title="Account Management API",
    description="API for managing accounts, hardware info, and authentication",
    version="1.0.0"
)

# Configure CORS
# Get allowed origins from environment variable or use default
allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:8084")
origins = [origin.strip() for origin in allowed_origins.split(",")]
print(f"CORS allowed origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)  # Auth router should be first for proper dependency resolution
app.include_router(accounts.router)
app.include_router(cards.router)
app.include_router(hardware.router)
app.include_router(steam_auth.router)
app.include_router(account_status.router)

@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}
