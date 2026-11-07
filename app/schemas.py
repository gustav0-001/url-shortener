from pydantic import BaseModel, ConfigDict, HttpUrl, computed_field, field_validator
from datetime import datetime
from app.config import settings
from urllib.parse import urlparse

class LinkCreate(BaseModel):
    """
    Схема создания ссылки
    """
    original_url: HttpUrl

    @field_validator("original_url")
    @classmethod
    def reject_own_domain(cls, value: HttpUrl) -> HttpUrl:
        own_host = urlparse(settings.base_url).hostname
        if value.host == own_host:
            raise ValueError("Links to this service are not allowed")
        return value


class LinkResponse(BaseModel):
    """
    Схема ответа: данные ссылки и готовый короткий адрес
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    short_code: str
    original_url: str
    clicks: int
    created_at: datetime

    @computed_field
    @property
    def short_url(self) -> str:
        return f"{settings.base_url.rstrip('/')}/{self.short_code}"