"""Оркестрация: валидация -> модель -> ПРИКЛАДНЫЕ ПРАВИЛА -> результат."""
from __future__ import annotations

import uuid
from typing import Optional

from app.inference import RawRecommendation, Recommender
from app.preprocessing import normalize_cart, normalize_id
from app.schemas import (
    ModelUnavailableError, PredictionRequest, PredictionResult, RecommendedItem,
)

SCORE_THRESHOLD = 0.20

class RecommendationService:
    def __init__(self, recommender: Optional[Recommender] = None):
        self._recommender = recommender or Recommender()

    @property
    def model_version(self) -> str:
        return self._recommender.version

    def recommend(self, request: PredictionRequest) -> PredictionResult:
        try:
            raw = self._recommender.predict(request.item_id, limit=200)
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
        cart = normalize_cart(request.current_cart_items)
        current = normalize_id(request.item_id)

        filtered = [
            c for c in candidates
            if normalize_id(c.item_id) not in cart
            and normalize_id(c.item_id) != current
            and c.score >= SCORE_THRESHOLD
        ]

        if not filtered:
            filtered = [
                c for c in self._recommender.popular()
                if normalize_id(c.item_id) not in cart
                and normalize_id(c.item_id) != current
            ]

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
            recommendations=[RecommendedItem(item_id=c.item_id, score=c.score)
                             for c in filtered[:10]],
            model_version=model_version,
            manual_review_required=False,
        )
