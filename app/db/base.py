from sqlalchemy.orm import declarative_base

Base = declarative_base()

from app.models.audit import AuditEvent  # noqa
