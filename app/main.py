from fastapi import FastAPI

from app.routers.auth import router as auth_router

from app.routers.requests import router as requests_router

app = FastAPI(title="AccessOps API")

app.include_router(auth_router)

app.include_router(requests_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


def jwt_secret() -> str:
    s = os.getenv("JWT_SECRET", "").strip()
    if not s:
        # safe default for local dev/test; production should always set env
        if os.getenv("ENV", "").lower() in {"test", "dev", "local"}:
            return "dev-secret-for-tests"
        raise RuntimeError("JWT_SECRET is required")
    return s