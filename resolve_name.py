# # resolve_name.py
import json
from pathlib import Path
# from rapidfuzz import fuzz, process

# def normalize_name(name: str) -> str:
#     if not name:
#         return ""
#     return name.strip().lower().replace(".", "").replace(",", "")

# def load_user_index(path="data/user_index.json"):
#     """Load the saved usernames."""
#     if not Path(path).exists():
#         raise FileNotFoundError(f"{path} not found — please run build_user_index.py first.")
#     with open(path) as f:
#         return json.load(f)

# def resolve_user_name(query_name: str, all_names: list[str], base_threshold: int = 70):
#     query_name = query_name.lower().strip()
#     names_lower = [n.lower() for n in all_names]

#     best_match, score, _ = process.extractOne(query_name, names_lower)

#     if best_match and query_name in best_match:
#         score = max(score, 85)

#     first_name = best_match.split()[0] if best_match else ""
#     if query_name == first_name:
#         score = max(score, 90)

#     if score >= base_threshold:
#         return best_match, score
#     else:
#         return None, score

# if __name__ == "__main__":
#     user_index = load_user_index()
#     test_queries = ["Layyla", "Amina", "Hans", "Fatma", "Kawaguchi"]
#     for q in test_queries:
#         match = resolve_user_name(q, user_index)
#         print(f"Query: {q:10s} → Match: {match}")
# resolve_name.py
# resolve_name.py — refined

# robust_resolve_name.py

# name_resolver_structured.py
from rapidfuzz import fuzz
import re

def normalize(name: str):
    if not name:
        return ""
    name = name.lower().strip()
    name = re.sub(r"[’'`-]", " ", name)
    name = re.sub(r"\s+", " ", name)
    return name

def load_user_index(path="data/user_index.json"):
    """Load the saved usernames."""
    if not Path(path).exists():
        raise FileNotFoundError(f"{path} not found — please run build_user_index.py first.")
    with open(path) as f:
        return json.load(f)

def tokenize(name: str):
    return normalize(name).split()

def resolve_user_name(query_name: str, known_names: list[str], threshold: int = 85):
    if not query_name:
        return None, 0

    q_tokens = tokenize(query_name)
    if not q_tokens:
        return None, 0

    best_match, best_score = None, 0

    for candidate in known_names:
        c_tokens = tokenize(candidate)
        if not c_tokens:
            continue

        # --- 1️⃣ First-name comparison
        first_score = fuzz.ratio(q_tokens[0], c_tokens[0])

        # --- 2️⃣ Last-name comparison (if present)
        if len(q_tokens) > 1 and len(c_tokens) > 1:
            last_score = fuzz.ratio(q_tokens[-1], c_tokens[-1])
            avg_score = (first_score + last_score) / 2
        else:
            avg_score = first_score

        # --- 3️⃣ Optional middle/multi-token handling
        if len(q_tokens) > 2 and len(c_tokens) > 2:
            mid_score = fuzz.ratio(" ".join(q_tokens[1:-1]), " ".join(c_tokens[1:-1]))
            avg_score = (first_score + mid_score + last_score) / 3

        if avg_score > best_score:
            best_score = avg_score
            best_match = candidate

    return (best_match, round(best_score, 2)) if best_score >= threshold else (None, best_score)
