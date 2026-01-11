import os


def database_url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        return url
    return "postgresql+psycopg://accessops:accessops@localhost:5432/accessops"


def jwt_algorithm() -> str:
    return os.getenv("JWT_ALGORITHM", "HS256").strip() or "HS256"


def jwt_expires_minutes() -> int:
    raw = os.getenv("JWT_EXPIRES_MINUTES", "60").strip()
    try:
        return int(raw)
    except ValueError as e:
        raise RuntimeError("JWT_EXPIRES_MINUTES must be an integer") from e


def jwt_secret() -> str:
    s = os.getenv("JWT_SECRET", "").strip()
    if not s:
        raise RuntimeError("JWT_SECRET is required (set env var JWT_SECRET)")
    return s

