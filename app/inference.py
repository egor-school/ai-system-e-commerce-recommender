"""Инференс: обращение к модели, возврат сырых кандидатов. Без бизнес-правил."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from app.preprocessing import normalize_id
from app.schemas import ModelUnavailableError

DEFAULT_MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "cooccurrence.json"

@dataclass
class RawRecommendation:
    item_id: str
    score: float

@dataclass
class RawModelOutput:
    candidates: list[RawRecommendation]
    model_version: str

class Recommender:
    def __init__(self, model_path: Path = DEFAULT_MODEL_PATH):
        self._path = model_path
        self._model = self._load(model_path)

    @staticmethod
    def _load(path: Path) -> dict:
        if not path.exists():
            raise ModelUnavailableError(f"Model artifact not found: {path}")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise ModelUnavailableError(f"Corrupted model artifact: {exc}") from exc
        required = {"version", "cooc", "popular", "known_items"}
        if not required.issubset(data):
            raise ModelUnavailableError("Model artifact missing fields")
        return data

    @property
    def version(self) -> str:
        return self._model["version"]

    def predict(self, item_id: str, limit: int = 100) -> RawModelOutput:
        key = normalize_id(item_id)
        cooc = self._model["cooc"].get(key, {})
        candidates = [RawRecommendation(item_id=j, score=float(s))
                      for j, s in cooc.items()]
        candidates.sort(key=lambda r: r.score, reverse=True)
        return RawModelOutput(candidates=candidates[:limit],
                              model_version=self._model["version"])

    def popular(self) -> list[RawRecommendation]:
        return [RawRecommendation(item_id=p["item_id"], score=float(p["score"]))
                for p in self._model["popular"]]
