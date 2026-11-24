"""Демонстрация музыкальной рекомендательной системы."""
from pydantic import ValidationError
from app.schemas import PredictionRequest
from app.service import RecommendationService

def main() -> None:
    svc = RecommendationService()
    print(f"model_version = {svc.model_version}\n")

    # Сценарий 1: Фанат рока и энергичной музыки
    # (используем реальные ID, которые сгенерирует скрипт обучения)
    req1 = PredictionRequest(
        user_id="user_rock_fan", 
        history=["TRACK_001_ROCK", "TRACK_010_INDIE"]
    )
    print("--- Рекомендации для фаната рока ---")
    print(svc.recommend(req1).model_dump_json(indent=2), "\n")

    # Сценарий 2: Фанат спокойного джаза
    req2 = PredictionRequest(
        user_id="user_jazz_fan", 
        history=["TRACK_004_JAZZ"]
    )
    print("--- Рекомендации для фаната джаза ---")
    print(svc.recommend(req2).model_dump_json(indent=2), "\n")

    # Сценарий 3: Холодный старт (неизвестные треки в истории)
    req3 = PredictionRequest(
        user_id="user_new", 
        history=["TRACK_UNKNOWN_XYZ"]
    )
    print("--- Ручная проверка: холодный старт ---")
    print(svc.recommend(req3).model_dump_json(indent=2), "\n")

    # Сценарий 4: Ошибка валидации
    print("--- Ошибочный вход: пустая история ---")
    try:
        PredictionRequest(user_id="user_err", history=[])
    except ValidationError as e:
        print(f"Ожидаемая ошибка валидации: {e.errors()[0]['msg']}")

if __name__ == "__main__":
    main()
