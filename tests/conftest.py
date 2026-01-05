import os

def pytest_configure() -> None:
    # Ensure JWT works for any endpoint tests that require token issuance.
    os.environ.setdefault("JWT_SECRET", "dev-secret-for-tests")
