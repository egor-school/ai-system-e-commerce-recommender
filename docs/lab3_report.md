# Лабораторная работа № 3 — отчёт

## 1. Тема проекта и реализованный компонент
**Тема проекта (ЛР № 2):** «Персонализированная рекомендательная система E-Commerce Recommender» (Вариант 8, группа ЕТ-312, Шукшин Егор, Шевяков Александр).

**Реализованный компонент:** `app.services.prediction` — сервис генерации и ранжирования рекомендаций с fallback (резервным вариантом) на популярные товары. Компонент покрывает функциональные требования FR-01 (генерация рекомендаций) и FR-03 (обработка холодного старта).

## 2. Место на архитектурной схеме ЛР № 2
Компонент занимает место между слоем инференса (`app.ml.inference`) и слоем API (`app.api.routes`). Он принимает валидированный `PredictionRequest`, обращается к модели, применяет прикладные бизнес-правила и возвращает `PredictionResult`. 
В рамках данной ЛР веб-сервер (FastAPI) и база данных (PostgreSQL) не реализуются, так как целью является изолированный программный компонент.

```mermaid
flowchart LR
    Client[Клиент] -->|PredictionRequest| Service[app.service]
    Service -->|item_id| Inference[app.inference]
    Inference -->|JSON| Model[(models/cooccurrence.json)]
    Inference -->|RawModelOutput| Service
    Service -->|PredictionResult| Client

```
## 3. Входной и выходной контракт

**Вход (`PredictionRequest`):**
- `item_id` (строка, ID текущего товара)
- `user_id` (строка, ID пользователя)
- `current_cart_items` (список строк, товары в корзине)

**Выход (`PredictionResult`):**
- `request_id` (UUIDv4 для аудита)
- `user_id`
- `recommendations` (список объектов `{item_id, score}`, где `score` от 0.0 до 1.0)
- `model_version` (версия модели, выдавший прогноз)
- `manual_review_required` (флаг необходимости ручной проверки)

**Ошибки:**
- `pydantic.ValidationError` — неверный вход (пустой ID, неверный тип данных).
- `ModelUnavailableError` — артефакт модели отсутствует или поврежден.

## 4. Используемая модель и источник тестовых данных

**Модель:** Baseline-модель на основе алгоритма **Item-to-Item Co-occurrence** (совместная встречаемость товаров). Модель не использует нейросети и обучается за счет подсчета частот совместных покупок.

**Артефакт:** Веса сохраняются в безопасном формате `models/cooccurrence.json` (без использования pickle).

**Источник данных:** Синтетический мини-датасет (10 пользователей × 1-3 товара), зашитый в скрипт обучения `scripts/train_model.py`. Персональные данные отсутствуют.

## 5. Команда установки зависимостей и локального запуска

```bash
# 1. Создание и активация окружения
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate

# 2. Установка зависимостей
pip install -r requirements.txt

# 3. Обучение модели (создание models/cooccurrence.json)
python -m scripts.train_model

# 4. Запуск тестов (8 проверок)
python -m pytest -q

# 5. Демонстрация работы
python demo.py
```
## 6. Таблица тестовых случаев и результатов

**Схема прохождения тестового сценария:**
```mermaid
sequenceDiagram
    participant T as Тест (pytest)
    participant S as RecommendationService
    participant R as Recommender (Модель)
    
    T->>S: recommend(PredictionRequest)
    S->>R: predict(item_id)
    
    alt Модель недоступна (битый JSON)
        R-->>S: raise ModelUnavailableError
        S-->>T: ModelUnavailableError (Тест 4 пройден)
    else Модель доступна
        R-->>S: RawModelOutput (кандидаты)
        S->>S: Применение правил (фильтрация, fallback)
        S-->>T: PredictionResult (Тесты 1, 2, 3, 5 пройдены)
    end
```

**Сводная таблица результатов:**

| Сценарий | Входные данные | Ожидание | Результат |
|---|---|---|---|
| 1. Валидный запрос | `PROD_PHONE`, `u1` | Корректный ответ со скором 0..1 | PASSED |
| 2. Разные товары | `PROD_PHONE` и `PROD_LAPTOP` | Списки рекомендаций отличаются | PASSED |
| 3. Неверный ввод | Пустой `user_id`, `item_id`, пробелы | Ошибка `ValidationError` | PASSED |
| 4. Fallback | `PROD_UNKNOWN` | Список популярных, `review=False` | PASSED |
| 5. Нет артефакта | Путь к несуществующему файлу | Ошибка `ModelUnavailableError` | PASSED |
| 6. Битый JSON | Файл с невалидным содержимым | Ошибка `ModelUnavailableError` | PASSED |

## 7. Ограничения компонента и ожидаемое развитие на следующих лабораторных

**Ограничения:**
- Модель является baseline (точность Recall@K, NDCG не измеряется).
- Синтетический мини-датасет (10 строк) не отражает реальное поведение покупателей.
- Нет ANN-поиска, CatBoost, Redis, DVC, PostgreSQL и Docker.

**План развития:**

```mermaid
gantt
    title План развития AI-системы
    dateFormat  YYYY-MM-DD
    axisFormat  %m-%d
    section ЛР № 3 (Текущая)
    Изолированный компонент и тесты :done,    des1, 2026-10-01, 2026-10-15
    section Следующие ЛР
    Воспроизводимый конвейер данных (DVC) :active,  des2, 2026-10-16, 2026-10-30
    Контейнеризация (Docker)              :         des3, 2026-11-01, 2026-11-15
    REST API (FastAPI) и CI/CD            :         des4, 2026-11-16, 2026-11-30

```

## 8. Изменения архитектуры ЛР № 2, если они потребовались

Изменения минимальны и не нарушают исходную архитектуру:

1. В контракт добавлено поле `manual_review_required` для сценариев деградации.
2. Модель из ЛР № 2 (CatBoost + ANN) заменена на baseline co-occurrence для соответствия ограничениям по времени (4 часа) согласно ТЗ.
3. Поле `device_type` в ЛР № 3 не используется, так как не влияет на логику инференса.
