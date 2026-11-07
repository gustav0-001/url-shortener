from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlmodel import SQLModel, Field


def get_current_time():
    return datetime.now(timezone.utc)


class Link(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    short_code: str = Field(unique=True)
    original_url: str
    clicks: int = Field(default=0)
    created_at: datetime = Field(
        default_factory=get_current_time,
        sa_type=DateTime(timezone=True),
    )