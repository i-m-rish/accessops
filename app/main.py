from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.routers.auth import router as auth_router
from app.routers.requests import router as requests_router
from app.routers.user_admin import router as role_router

app = FastAPI(title="AccessOps API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router)
app.include_router(requests_router)
app.include_router(role_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


def jwt_secret() -> str:
    s = os.getenv("JWT_SECRET", "").strip()
    if not s:
        if os.getenv("ENV", "").lower() in {"test", "dev", "local"}:
            return "dev-secret-for-tests"
        raise RuntimeError("JWT_SECRET is required")
    return s