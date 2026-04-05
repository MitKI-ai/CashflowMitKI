from datetime import datetime

from pydantic import BaseModel

VALID_PROVIDERS = {"anthropic", "openrouter"}


class LLMProviderCreate(BaseModel):
    provider: str  # anthropic, openrouter
    api_key: str
    model_id: str


class LLMProviderUpdate(BaseModel):
    model_id: str | None = None
    api_key: str | None = None
    is_active: bool | None = None


class LLMProviderResponse(BaseModel):
    id: str
    provider: str
    model_id: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
