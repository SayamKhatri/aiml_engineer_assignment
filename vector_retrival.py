import google.generativeai as genai
import os
from dotenv import load_dotenv
import chromadb

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def chroma_search(query, user_name=None, category=None, top_k=40):
    query_emb = genai.embed_content(
        model="models/embedding-001",
        content=query,
        task_type="retrieval_query"
    )["embedding"]

    # ✅ Normalize category if it's a list
    if isinstance(category, list):
        # Just take the first category if one-element list
        # (main.py already loops if there are multiple)
        category = category[0] if category else None

    # ✅ Normalize casing & whitespace for consistent Chroma matching
    if user_name:
        user_name = user_name.strip().title()  # e.g. "vikram desai" → "Vikram Desai"
    if category:
        category = category.strip()

    # Connect to Chroma store 
    chroma_client = chromadb.PersistentClient(path="data/chroma_store")
    collection = chroma_client.get_collection("member_messages")

    def run_query(where_filter):
        results = collection.query(
            query_embeddings=[query_emb],
            n_results=top_k,
            where=where_filter if where_filter else {}
        )
        docs = results["documents"][0]
        metas = results["metadatas"][0]
        return [{"message": d, **m} for d, m in zip(docs, metas) if d]

    if user_name and category:
        where = {
            "$and": [
                {"user_name": {"$eq": user_name}},
                {"category": {"$eq": category}}
            ]
        }
        results = run_query(where)
        if results:
            return results
        print("No results for user+category, retrying with user only...")

    if user_name:
        where = {"user_name": {"$eq": user_name}}
        results = run_query(where)
        if results:
            return results
        print("No results for user only, retrying with category only...")

    if category:
        where = {"category": {"$eq": category}}
        results = run_query(where)
        if results:
            return results

    print("No results found in any fallback level.")
    return []
