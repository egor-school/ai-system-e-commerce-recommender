"""Тесты компонента. Без сети и без веб-сервера."""
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.inference import Recommender
from app.schemas import ModelUnavailableError, PredictionRequest
from app.service import RecommendationService

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "cooccurrence.json"

@pytest.fixture(scope="module", autouse=True)
def ensure_model():
    if not MODEL_PATH.exists():
        from scripts.train_model import main as train
        train()
    assert MODEL_PATH.exists()

@pytest.fixture()
def service():
    return RecommendationService()

def test_valid_request(service):
    res = service.recommend(PredictionRequest(item_id="PROD_PHONE", user_id="u1"))
    assert res.model_version == service.model_version
    assert isinstance(res.request_id, str) and res.request_id
    assert len(res.recommendations) >= 1
    for r in res.recommendations:
        assert 0.0 <= r.score <= 1.0

def test_different_item_different_result(service):
    r1 = service.recommend(PredictionRequest(item_id="PROD_PHONE", user_id="u1"))
    r2 = service.recommend(PredictionRequest(item_id="PROD_LAPTOP", user_id="u4"))
    ids1 = {r.item_id for r in r1.recommendations}
    ids2 = {r.item_id for r in r2.recommendations}
    assert ids1 != ids2

@pytest.mark.parametrize("payload", [
    {"item_id": "PROD_PHONE", "user_id": ""},
    {"item_id": "", "user_id": "u1"},
    {"item_id": "PROD_PHONE", "user_id": "   "},
])
def test_invalid_input_rejected(payload):
    with pytest.raises(ValidationError):
        PredictionRequest(**payload)

def test_missing_model_raises():
    with pytest.raises(ModelUnavailableError):
        Recommender(model_path=Path("/nonexistent/cooccurrence.json"))

def test_corrupted_model_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{ not json")
    with pytest.raises(ModelUnavailableError):
        Recommender(model_path=bad)

def test_cold_start_fallback(service):
    res = service.recommend(PredictionRequest(item_id="PROD_UNKNOWN", user_id="new"))
    assert res.manual_review_required is False
    assert len(res.recommendations) >= 1
