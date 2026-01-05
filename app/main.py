from fastapi import FastAPI

from app.routers.auth import router as auth_router

from app.routers.requests import router as requests_router

app = FastAPI(title="AccessOps API")

app.include_router(auth_router)

app.include_router(requests_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
