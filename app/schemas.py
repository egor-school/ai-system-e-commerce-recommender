"""Входной и выходной контракты компонента рекомендаций."""
from typing import List

from pydantic import BaseModel, Field, field_validator


class PredictionRequest(BaseModel):
    item_id: str = Field(min_length=1, max_length=64)
    user_id: str = Field(min_length=1, max_length=64)
    current_cart_items: List[str] = Field(default_factory=list)

    @field_validator("user_id", "item_id")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be blank")
        return v.strip()


class RecommendedItem(BaseModel):
    item_id: str
    score: float = Field(ge=0.0, le=1.0)


class PredictionResult(BaseModel):
    request_id: str
    user_id: str
    recommendations: List[RecommendedItem]
    model_version: str
    manual_review_required: bool


class ModelUnavailableError(RuntimeError):
    """Артефакт модели отсутствует или повреждён."""
