"""Инференс: поиск похожих треков по бинарным векторам из истории пользователя."""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path

from app.preprocessing import normalize_id
from app.schemas import ModelUnavailableError

DEFAULT_MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "music_model.json"

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
        required = {"version", "keywords", "vectors", "popular"}
        if not required.issubset(data):
            raise ModelUnavailableError("Model artifact missing fields")
        return data

    @property
    def version(self) -> str:
        return self._model["version"]

    def _build_user_profile(self, history: list[str]) -> list[int]:
        profile = [0] * len(self._model["keywords"])
        for track_id in history:
            key = normalize_id(track_id)
            if key in self._model["vectors"]:
                track_vec = self._model["vectors"][key]
                profile = [p + t for p, t in zip(profile, track_vec)]
        return [1 if p > 0 else 0 for p in profile]

    def _similarity(self, user_profile: list[int], track_vec: list[int]) -> float:
        matches = sum(1 for a, b in zip(user_profile, track_vec) if a == 1 and b == 1)
        total_tags_in_profile = sum(user_profile)
        return (matches / total_tags_in_profile) if total_tags_in_profile > 0 else 0.0

    def predict(self, history: list[str], limit: int = 10) -> RawModelOutput:
        user_profile = self._build_user_profile(history)
        
        if sum(user_profile) == 0:
            return RawModelOutput(candidates=[], model_version=self._model["version"])

        candidates = []
        history_keys = {normalize_id(h) for h in history}

        for other_id, other_vec in self._model["vectors"].items():
            if other_id in history_keys:
                continue 
            
            score = self._similarity(user_profile, other_vec)
            if score > 0.0:
                candidates.append(RawRecommendation(item_id=other_id, score=round(score, 4)))

        candidates.sort(key=lambda r: r.score, reverse=True)
        return RawModelOutput(candidates=candidates[:limit], model_version=self._model["version"])

    def popular(self) -> list[RawRecommendation]:
        return [RawRecommendation(item_id=p["item_id"], score=float(p["score"]))
                for p in self._model["popular"]]
