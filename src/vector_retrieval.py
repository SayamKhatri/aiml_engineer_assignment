import google.generativeai as genai
import os
from dotenv import load_dotenv
import chromadb

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


def get_data_path(relative_path):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, relative_path)


def chroma_search(query, user_name=None, category=None, top_k=25):
    query_emb = genai.embed_content(
        model="models/embedding-001",
        content=query,
        task_type="retrieval_query"
    )["embedding"]

    if isinstance(category, list):
        category = category[0] if category else None

    if user_name:
        user_name = user_name.strip().title()
    if category:
        category = category.strip()

    chroma_path = get_data_path("data/chroma_store")
    chroma_client = chromadb.PersistentClient(path=chroma_path)
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

    if user_name:
        where = {"user_name": {"$eq": user_name}}
        results = run_query(where)
        if results:
            return results

    if category:
        where = {"category": {"$eq": category}}
        results = run_query(where)
        if results:
            return results

    return []
