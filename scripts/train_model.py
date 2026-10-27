"""Разовое обучение item-to-item co-occurrence на мини-датасете."""
import json
from collections import Counter, defaultdict
from pathlib import Path

from app.preprocessing import normalize_id

MODEL_VERSION = "cooc-v1"
OUTPUT = Path(__file__).resolve().parent.parent / "models" / "cooccurrence.json"

USER_HISTORY = {
    "u1": ["PROD_PHONE", "PROD_CASE", "PROD_CHARGER"],
    "u2": ["PROD_PHONE", "PROD_CASE"],
    "u3": ["PROD_PHONE", "PROD_HEADPHONES"],
    "u4": ["PROD_LAPTOP", "PROD_MOUSE", "PROD_BAG"],
    "u5": ["PROD_LAPTOP", "PROD_MOUSE"],
    "u6": ["PROD_LAPTOP", "PROD_BAG"],
    "u7": ["PROD_HEADPHONES", "PROD_CHARGER"],
    "u8": ["PROD_MOUSE", "PROD_BAG"],
    "u9": ["PROD_PHONE", "PROD_HEADPHONES", "PROD_CASE"],
    "u10": ["PROD_LAPTOP"],
}

def main() -> None:
    co: dict[str, Counter] = defaultdict(Counter)
    popularity: Counter = Counter()

    for items in USER_HISTORY.values():
        norm = [normalize_id(x) for x in items]
        for i in norm:
            popularity[i] += 1
            for j in norm:
                if i != j:
                    co[i][j] += 1

    cooc = {}
    for i, counter in co.items():
        total = sum(counter.values())
        cooc[i] = {j: round(c / total, 4) for j, c in counter.items()}

    top_popular = [{"item_id": k, "score": round(v / max(popularity.values()), 4)}
                   for k, v in popularity.most_common(10)]

    payload = {
        "version": MODEL_VERSION,
        "cooc": cooc,
        "popular": top_popular,
        "known_items": sorted(popularity.keys()),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    print(f"Model saved: {OUTPUT} (version {MODEL_VERSION})")

if __name__ == "__main__":
    main()
