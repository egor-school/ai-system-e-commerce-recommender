"""Подготовка признаков. Та же функция используется при обучении и инференсе."""
import re

_WS = re.compile(r"\s+")


def normalize_id(raw: str) -> str:
    return _WS.sub("", raw).strip().upper()


def normalize_cart(items: list[str]) -> set[str]:
    return {normalize_id(x) for x in items if x}
