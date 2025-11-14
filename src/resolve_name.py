import json
import os
from pathlib import Path
from rapidfuzz import fuzz
import re


def get_data_path(relative_path):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, relative_path)


def normalize(name: str):
    if not name:
        return ""
    name = name.lower().strip()
    name = re.sub(r"[''`-]", " ", name)
    name = re.sub(r"\s+", " ", name)
    return name


def load_user_index(path="data/user_index.json"):
    """Load the saved usernames."""
    abs_path = get_data_path(path)
    if not Path(abs_path).exists():
        raise FileNotFoundError(f"{abs_path} not found")
    with open(abs_path) as f:
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

        first_score = fuzz.ratio(q_tokens[0], c_tokens[0])

        if len(q_tokens) > 1 and len(c_tokens) > 1:
            last_score = fuzz.ratio(q_tokens[-1], c_tokens[-1])
            avg_score = (first_score + last_score) / 2
        else:
            avg_score = first_score

        if len(q_tokens) > 2 and len(c_tokens) > 2:
            mid_score = fuzz.ratio(" ".join(q_tokens[1:-1]), " ".join(c_tokens[1:-1]))
            avg_score = (first_score + mid_score + last_score) / 3

        if avg_score > best_score:
            best_score = avg_score
            best_match = candidate

    return (best_match, round(best_score, 2)) if best_score >= threshold else (None, best_score)
