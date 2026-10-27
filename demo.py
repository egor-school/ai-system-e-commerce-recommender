"""Демонстрация: 2 корректных входа, 1 ошибочный, 1 сценарий передачи человеку."""
from pydantic import ValidationError

from app.schemas import PredictionRequest
from app.service import RecommendationService


def main() -> None:
    svc = RecommendationService()
    print(f"model_version = {svc.model_version}\n")

    for label, payload in [
        ("Корректный #1: смотрим телефон",
         {"item_id": "PROD_PHONE", "user_id": "u1"}),
        ("Корректный #2: смотрим ноутбук, мышь уже в корзине",
         {"item_id": "PROD_LAPTOP", "user_id": "u4",
          "current_cart_items": ["PROD_MOUSE"]}),
        ("Ручная проверка: неизвестный товар (fallback или отказ)",
         {"item_id": "PROD_UNKNOWN", "user_id": "new"}),
    ]:
        print(f"--- {label} ---")
        result = svc.recommend(PredictionRequest(**payload))
        print(result.model_dump_json(indent=2), "\n")

    print("--- Ошибочный вход: пустой user_id ---")
    try:
        PredictionRequest(item_id="PROD_PHONE", user_id="")
    except ValidationError as e:
        print(f"Ожидаемая ошибка валидации: {e.errors()[0]['msg']}")


if __name__ == "__main__":
    main()
