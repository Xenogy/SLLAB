from fastapi import FastAPI
from app.router import router as steam_checker_router # This import should now work

app = FastAPI(
    title="Steam Profile Ban Checker API",
    description="API to check Steam profiles for bans, with proxy and retry support.",
    version="1.0.0"
)

app.include_router(steam_checker_router, prefix="/api/v1/steam", tags=["Steam Checker"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Steam Profile Ban Checker API. See /docs for endpoints."}