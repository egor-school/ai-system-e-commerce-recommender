"""Оркестрация: валидация -> модель -> ПРИКЛАДНЫЕ ПРАВИЛА -> результат."""
from __future__ import annotations
import uuid
from typing import Optional

from app.inference import RawRecommendation, Recommender
from app.schemas import (
    ModelUnavailableError, PredictionRequest, PredictionResult, RecommendedItem,
)

SCORE_THRESHOLD = 0.01

class RecommendationService:
    def __init__(self, recommender: Optional[Recommender] = None):
        self._recommender = recommender or Recommender()

    @property
    def model_version(self) -> str:
        return self._recommender.version

    def recommend(self, request: PredictionRequest) -> PredictionResult:
        try:
            # ВОТ ЗДЕСЬ ИЗМЕНЕНИЕ: передаем request.history
            raw = self._recommender.predict(request.history, limit=200)
        except ModelUnavailableError:
            raise
        except Exception as exc:
            raise ModelUnavailableError(f"model inference failed: {exc}") from exc
        return self._apply_rules(request, raw.candidates, raw.model_version)

    def _apply_rules(
        self,
        request: PredictionRequest,
        candidates: list[RawRecommendation],
        model_version: str,
    ) -> PredictionResult:
        # Фильтрация по порогу скора
        filtered = [c for c in candidates if c.score >= SCORE_THRESHOLD]

        # Fallback на популярное (если пусто)
        if not filtered:
            filtered = self._recommender.popular()

        # Отказ, если и популярного нет (вырожденный артефакт)
        if not filtered:
            return PredictionResult(
                request_id=str(uuid.uuid4()),
                user_id=request.user_id,
                recommendations=[],
                model_version=model_version,
                manual_review_required=True,
            )

        return PredictionResult(
            request_id=str(uuid.uuid4()),
            user_id=request.user_id,
            recommendations=[RecommendedItem(item_id=c.item_id, score=c.score) for c in filtered[:10]],
            model_version=model_version,
            manual_review_required=False,
        )
