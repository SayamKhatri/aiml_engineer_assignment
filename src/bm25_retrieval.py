from rank_bm25 import BM25Okapi
from nltk.tokenize import word_tokenize
import numpy as np
import nltk

nltk.download('punkt_tab', quiet=True)


def bm25_search(query, messages, user_name=None, category=None, top_k=30):
    def filter_messages(u=None, c=None):
        return [
            m for m in messages
            if (not u or m["user_name"].lower().strip() == u.lower().strip())
            and (not c or m["category"].strip() == c.strip())
        ]

    filtered = filter_messages(user_name, category)

    if not filtered and user_name:
        print("No results for user+category, retrying with user only...")
        filtered = filter_messages(user_name)

    if not filtered:
        print("No results found for this user/category combination.")
        return []

    corpus = [m["message"] for m in filtered]
    tokenized_corpus = [word_tokenize(doc.lower()) for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)

    scores = bm25.get_scores(word_tokenize(query.lower()))
    top_indices = np.argsort(scores)[::-1][:top_k]

    return [filtered[i] for i in top_indices]

