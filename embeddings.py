
import google.generativeai as genai
import chromadb
import json
import os
from dotenv import load_dotenv
load_dotenv()

genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

with open("data/messages_with_categories.json") as f:
    messages = json.load(f)

texts = [m["message"] for m in messages]
metadatas = [
    {
        "user_id": m["user_id"],
        "user_name": m["user_name"],
        "timestamp": m["timestamp"],
        "category": m["category"]
    }
    for m in messages
]
ids = [str(m["id"]) for m in messages]  

embeddings_list = []
for text in texts:
    result = genai.embed_content(
        model="models/embedding-001",
        content=text,
        task_type="retrieval_document"  
    )
    embeddings_list.append(result["embedding"])

print(f"Generated {len(embeddings_list)} embeddings.")

chroma_client = chromadb.PersistentClient(path="data/chroma_store")
collection = chroma_client.get_or_create_collection(name="member_messages")

collection.add(
    documents=texts,
    embeddings=embeddings_list,
    metadatas=metadatas,
    ids=ids
)

print(f"Stored {len(ids)} messages in ChromaDB with Gemini embeddings.")
