"""Тесты компонента рекомендаций. Без сети и без веб-сервера."""
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.inference import Recommender
from app.schemas import ModelUnavailableError, PredictionRequest
from app.service import RecommendationService

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "music_model.json"


@pytest.fixture(scope="module", autouse=True)
def ensure_model():
    """Если модели нет — генерируем её перед запуском тестов."""
    if not MODEL_PATH.exists():
        from scripts.train_model import main as train
        train()
    assert MODEL_PATH.exists()


@pytest.fixture()
def service():
    return RecommendationService()


# Тест 1. Корректный запрос -> валидный результат установленной схемы.
def test_valid_request(service):
    # Используем ID, которые точно сгенерирует скрипт обучения
    res = service.recommend(PredictionRequest(
        user_id="user_1", 
        history=["TRACK_001_ROCK", "TRACK_010_INDIE"]
    ))
    assert res.model_version == service.model_version
    assert isinstance(res.request_id, str) and res.request_id
    assert len(res.recommendations) >= 1
    for r in res.recommendations:
        assert 0.0 <= r.score <= 1.0


# Тест 2. Второй вход -> ОТЛИЧАЮЩЕЕСЯ поведение (разные вкусы).
def test_different_history_different_result(service):
    # Рокер
    r1 = service.recommend(PredictionRequest(
        user_id="user_rock", 
        history=["TRACK_001_ROCK"]
    ))
    # Джазмен
    r2 = service.recommend(PredictionRequest(
        user_id="user_jazz", 
        history=["TRACK_004_JAZZ"]
    ))
    
    ids1 = {r.item_id for r in r1.recommendations}
    ids2 = {r.item_id for r in r2.recommendations}
    # Наборы рекомендованных треков должны различаться
    assert ids1 != ids2


# Тест 3. Неверное/пограничное значение обрабатывается контролируемо.
@pytest.mark.parametrize("payload", [
    {"user_id": "u1", "history": []},          # пустая история
    {"user_id": "", "history": ["TRACK_001_ROCK"]},  # пустой user_id
    {"user_id": "u1", "history": [""]},        # пустой ID внутри истории
])
def test_invalid_input_rejected(payload):
    with pytest.raises(ValidationError):
        PredictionRequest(**payload)


# Тест 4. Сбой модели / отсутствие артефакта -> честная ошибка, не ложный успех.
def test_missing_model_raises():
    with pytest.raises(ModelUnavailableError):
        Recommender(model_path=Path("/nonexistent/music_model.json"))


def test_corrupted_model_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("{ not json")
    with pytest.raises(ModelUnavailableError):
        Recommender(model_path=bad)


# Тест 5. Сценарий передачи решения человеку: холодный старт -> fallback.
def test_cold_start_fallback(service):
    # Неизвестный трек в истории (модель не знает его тегов)
    res = service.recommend(PredictionRequest(
        user_id="new_user", 
        history=["TRACK_UNKNOWN_999"]
    ))
    # Должен сработать fallback (популярные треки), флаг ручной проверки False
    assert res.manual_review_required is False
    assert len(res.recommendations) >= 1
