from typing import List
from pydantic import BaseModel, Field, field_validator

class PredictionRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=64)
    history: List[str] = Field(min_length=1, description="ID прослушанных/лайкнутых треков")

    @field_validator("history")
    @classmethod
    def check_history_not_empty(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("history cannot be empty")
        # Добавляем проверку, что каждый элемент в списке не пустой
        for track_id in v:
            if not track_id.strip():
                raise ValueError("track IDs in history must not be blank")
        return v

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
