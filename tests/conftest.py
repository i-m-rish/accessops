import os
import pytest

@pytest.fixture(autouse=True)
def _test_env() -> None:
    # Provide deterministic JWT config for the entire test suite.
    os.environ.setdefault("JWT_SECRET", "test-secret-change-me")
    os.environ.setdefault("JWT_ALGORITHM", "HS256")
    os.environ.setdefault("JWT_EXPIRES_MINUTES", "60")


@pytest.fixture(autouse=True)
def _default_jwt_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    # Only set a default if the test hasn't explicitly removed/overridden it.
    if "JWT_SECRET" not in os.environ:
        monkeypatch.setenv("JWT_SECRET", "dev-secret-for-tests")
