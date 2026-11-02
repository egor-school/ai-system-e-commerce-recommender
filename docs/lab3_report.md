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
