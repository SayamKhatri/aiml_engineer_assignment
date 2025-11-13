from langgraph.graph import StateGraph, END
import json
from extractor import extract_metadata
from vector_retrival import chroma_search
from BM25_Retrieval import bm25_search
from typing import TypedDict, List, Dict, Any
from resolve_name import load_user_index, resolve_user_name
from prompt_builder import build_strong_prompt
import google.generativeai as genai
from langchain_groq import ChatGroq

from dotenv import load_dotenv
import os

USER_INDEX = load_user_index()
load_dotenv()
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.2,
    max_tokens=500
)

with open("data/messages_with_categories.json") as f:
    messages = json.load(f)

class QAState(TypedDict, total=False):
    query: str
    metadata: dict
    chroma_results: List[Dict[str, Any]]
    bm25_results: List[Dict[str, Any]]
    final_results: List[Dict[str, Any]]

def extractor_node(state):
    query = state["query"]
    meta = extract_metadata(query)
    print(meta.model_dump())
    resolved_name = resolve_user_name(meta.user_name, USER_INDEX)
    resolved_name = resolved_name[0]
    if resolved_name and resolved_name.lower() != (meta.user_name or "").lower():
        print(f"Fuzzy-resolved name: '{meta.user_name}' → '{resolved_name}'")
        meta.user_name = resolved_name.lower()
    elif not resolved_name and meta.user_name:
        print(f"No confident match for '{meta.user_name}' — category-only search.")
        meta.user_name = None
    elif resolved_name:
        meta.user_name = resolved_name.lower()

    return {"query": query, "metadata": meta.model_dump()}

def chroma_node(state):
    q, m = state["query"], state["metadata"]
    categories = m.get("category", [])
    if isinstance(categories, str):
        categories = [categories]

    results = []
    for cat in categories or [None]:  # fallback to None if empty
        results += chroma_search(q, m.get("user_name"), cat)
    return {"chroma_results": results}


def bm25_node(state):
    q, m = state["query"], state["metadata"]
    categories = m.get("category", [])
    if isinstance(categories, str):
        categories = [categories]

    results = []
    for cat in categories or [None]:
        results += bm25_search(q, messages, m.get("user_name"), cat)
    return {"bm25_results": results}



def merge_node(state):
    bm25 = state.get("bm25_results", [])
    chroma = state.get("chroma_results", [])
    combined = {r["message"]: r for r in (bm25 + chroma)}.values()
    return {"final_results": list(combined)}

graph = StateGraph(QAState)

graph.add_node("extractor", extractor_node)
graph.add_node("chroma", chroma_node)
graph.add_node("bm25", bm25_node)
graph.add_node("merge", merge_node)

graph.add_edge("extractor", "chroma")
graph.add_edge("extractor", "bm25")
graph.add_edge("chroma", "merge")
graph.add_edge("bm25", "merge")
graph.add_edge("merge", END)

graph.set_entry_point("extractor")
qa_pipeline = graph.compile()


if __name__ == "__main__":
    user_query = "What do we know about Layla's spouse and family members?"
    result = qa_pipeline.invoke({"query": user_query})
    
    print("\nExtracted Metadata:")
    print(result["metadata"])
    
    print("\nTop Combined Results:")
    for i, item in enumerate(result["final_results"], 1):
        print(f"{i}. {item['user_name']} — {item['category']} — {item['message']}")

    llm_prompt = build_strong_prompt(
        final_results=result["final_results"],
        metadata=result["metadata"],
        user_query=user_query,
        top_k=80
    )


    response = llm.invoke(llm_prompt)
    print("\n--- FINAL LLM ANSWER ---\n")
    print(response.content)
