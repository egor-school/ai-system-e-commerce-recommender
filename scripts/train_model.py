import json
import random
from pathlib import Path

MODEL_VERSION = "music-bow-v1"
OUTPUT = Path(__file__).resolve().parent.parent / "models" / "music_model.json"

KEYWORDS = [
    "rock", "pop", "rap", "jazz", "classical", "electronic", 
    "calm", "energetic", "sad", "happy", "dance", "guitar"
]

TAG_PROFILES = {
    "rock":      ["rock", "energetic", "guitar"],
    "pop":       ["pop", "happy", "dance"],
    "rap":       ["rap", "energetic", "dance"],
    "jazz":      ["jazz", "calm", "sad"],
    "classical": ["classical", "calm", "sad"],
    "electronic":["electronic", "energetic", "dance"],
    "indie":     ["rock", "pop", "sad", "guitar"],
    "chill":     ["electronic", "calm", "happy"]
}

def generate_dataset(num_tracks: int = 100) -> dict[str, list[str]]:
    random.seed(42)
    dataset = {}
    genres = list(TAG_PROFILES.keys())
    
    for i in range(num_tracks):
        genre = random.choice(genres)
        tags = list(TAG_PROFILES[genre])
        if random.random() > 0.5:
            extra_tag = random.choice(["happy", "sad", "calm", "energetic"])
            if extra_tag not in tags:
                tags.append(extra_tag)
        
        track_id = f"TRACK_{i+1:03d}_{genre.upper()}"
        dataset[track_id] = tags
    return dataset

def main() -> None:
    dataset = generate_dataset(100)
    vectors = {}

    for track_id, tags_list in dataset.items():
        vector = [1 if kw in tags_list else 0 for kw in KEYWORDS]
        vectors[track_id] = vector

    random.seed(42)
    popular_ids = random.sample(list(dataset.keys()), 10)

    payload = {
        "version": MODEL_VERSION,
        "keywords": KEYWORDS,
        "vectors": vectors,
        "popular": [{"item_id": tid, "score": 1.0} for tid in popular_ids]
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Model saved: {OUTPUT} (version {MODEL_VERSION}, {len(vectors)} tracks)")

if __name__ == "__main__":
    main()
