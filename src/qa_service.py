import json
import os
from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq

from src.extractor import extract_metadata
from src.vector_retrieval import chroma_search
from src.bm25_retrieval import bm25_search
from src.resolve_name import load_user_index, resolve_user_name
from src.prompt_builder import build_strong_prompt


class QAState(TypedDict, total=False):
    query: str
    metadata: dict
    chroma_results: List[Dict[str, Any]]
    bm25_results: List[Dict[str, Any]]
    final_results: List[Dict[str, Any]]


class QAService:
    def __init__(self, messages_path="data/messages_with_categories.json", user_index_path="data/user_index.json"):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        messages_path = os.path.join(base_dir, messages_path)
        user_index_path = os.path.join(base_dir, user_index_path)
        
        self.user_index = load_user_index(user_index_path)
        
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.2,
            max_tokens=500
        )
        
        with open(messages_path) as f:
            self.messages = json.load(f)
        
        self.pipeline = self._build_pipeline()
    
    def _extractor_node(self, state):
        query = state["query"]
        meta = extract_metadata(query)
        
        resolved_name = resolve_user_name(meta.user_name, self.user_index)
        resolved_name = resolved_name[0]
        
        if resolved_name and resolved_name.lower() != (meta.user_name or "").lower():
            meta.user_name = resolved_name.lower()
        elif not resolved_name and meta.user_name:
            meta.user_name = None
        elif resolved_name:
            meta.user_name = resolved_name.lower()

        return {"query": query, "metadata": meta.model_dump()}
    
    def _chroma_node(self, state):
        q, m = state["query"], state["metadata"]
        categories = m.get("category", [])
        if isinstance(categories, str):
            categories = [categories]

        results = []
        for cat in categories or [None]:
            results += chroma_search(q, m.get("user_name"), cat)
        return {"chroma_results": results}
    
    def _bm25_node(self, state):
        q, m = state["query"], state["metadata"]
        categories = m.get("category", [])
        if isinstance(categories, str):
            categories = [categories]

        results = []
        for cat in categories or [None]:
            results += bm25_search(q, self.messages, m.get("user_name"), cat)
        return {"bm25_results": results}
    
    def _merge_node(self, state):
        bm25 = state.get("bm25_results", [])
        chroma = state.get("chroma_results", [])
        combined = {r["message"]: r for r in (bm25 + chroma)}.values()
        return {"final_results": list(combined)}
    
    def _build_pipeline(self):
        graph = StateGraph(QAState)
        
        graph.add_node("extractor", self._extractor_node)
        graph.add_node("chroma", self._chroma_node)
        graph.add_node("bm25", self._bm25_node)
        graph.add_node("merge", self._merge_node)
        
        graph.add_edge("extractor", "chroma")
        graph.add_edge("extractor", "bm25")
        graph.add_edge("chroma", "merge")
        graph.add_edge("bm25", "merge")
        graph.add_edge("merge", END)
        
        graph.set_entry_point("extractor")
        return graph.compile()
    
    def answer_question(self, question: str) -> str:
        result = self.pipeline.invoke({"query": question})
        
        prompt = build_strong_prompt(
            final_results=result["final_results"],
            metadata=result["metadata"],
            user_query=question,
            top_k=80
        )
        
        response = self.llm.invoke(prompt)
        return response.content
