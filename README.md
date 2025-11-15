## **Project Overview**

This project implements a **question-answering system** that interprets natural-language questions about member data and generates accurate, context-aware answers.
The service is built with **FastAPI**, powered by **Groq’s LLaMA-3.3 (70B)** for reasoning, **Google Generative AI embeddings** for semantic search, and **ChromaDB** + **BM25** for hybrid retrieval.
The entire system is **containerized with Docker** and **deployed on Google Cloud Run**, making it publicly accessible via REST API.

-----
## **Try it Out**
**Backend API:**

```text
https://qa-service-226254600937.us-central1.run.app
```
**ChatBot UI URL:**

[https://aurora-assistant.lovable.app](https://aurora-assistant.lovable.app/)

-----
### System Design Summary

The overall system follows a **multi-stage pipeline** that converts an open-ended question into an exact, evidence-backed answer.
Below is the step-by-step architecture:


### 1. **Data Understanding & Automatic Categorization**

Before building the retrieval system, I performed **unsupervised clustering** to understand the message corpus and discover thematic structure.

* Embedded every message using `google-generativeai`’s `models/embedding-001`.
* Applied **K-Means clustering (k=24)** to group semantically similar messages.
* For each cluster:

  * Extracted **top keywords** and **representative examples**.
  * Queried an **LLM to infer a meaningful label**.
* After reviewing all 24 clusters, I consolidated them into **five broad, human-interpretable categories**:

  1. **Travel & Accommodation**
  2. **Dining & Experiences**
  3. **Personal & Wellness**
  4. **Account & Finance**
  5. **Transport & Mobility**

Each message in the Chroma store is indexed under these final categories.

---

### 2. **Metadata Extraction**

When a query arrives (e.g., *“What are Vikram’s dietary restrictions?”*),
the first stage runs **metadata extraction** via **LLaMA-3.3 on Groq**.

The model extracts:

* **`user_name`** — the person being asked about (if mentioned).
* **`category`** — up to **two** relevant categories:

  * one *direct* category explicitly implied,
  * one *reasoning-based* category inferred via semantic association.

Example:

> “What are Lorenzo’s pillow preferences?”
> → `["Personal & Wellness", "Travel & Accommodation"]`

This dual-category reasoning improves retrieval coverage for ambiguous intent.

---

### 3. **Name Resolution**

Since **ChromaDB** does not support fuzzy string matching, I implemented a custom resolver:

* Pre-indexed all known member names into `user_index.json`.
* Used **RapidFuzz** to perform similarity scoring between extracted name and known names.
* The system then substitutes the fuzzy match with the canonical name for precise filtering.

This step ensures that queries like “Vikram D.” still retrieve correct results.

---

### 4. **Hybrid Retrieval Layer**

Once metadata is resolved, two parallel retrieval paths are executed:

#### **A. Vector Search (Semantic Retrieval)**

* Queries are embedded using the same `models/embedding-001` model.
* Search is performed in **ChromaDB** with metadata filtering:

  * exact `user_name` match
  * matching `category` (one or both inferred categories)
* Retrieves top 20-30 messages ranked by cosine similarity.

#### **B. BM25 Search (Lexical Retrieval)**

* Runs over the same filtered subset.
* Captures messages with **keyword overlaps** missed by dense embeddings.

#### **Merging**

* Both result sets are combined, deduplicated by message text, and sorted by relevance.
* Typically 40–50 high-quality context messages are passed downstream.

---

### 5. **Answer Generation**

A custom prompt is built dynamically via the `prompt_builder` module:

* Includes extracted metadata, retrieved context, and the original user query.
* Contains strong **guardrails** to:

  * prevent hallucinations,
  * emphasize factual grounding in retrieved context,
  * and force concise, natural answers.

The final prompt is passed to the **Groq LLaMA-3.3 70B** model to produce the answer.

---

### 6. **API & Deployment**

* Exposed as a REST API (`/question`) using **FastAPI**.
* Containerized with **Docker** and deployed to **Google Cloud Run**.
* A minimal **Lovable front-end** provides a chat-style UI that connects to the API endpoint.

---

### **Alternative Approaches Considered**

| Approach                    | Why Rejected                                                           |
| --------------------------- | ---------------------------------------------------------------------- |
| Fine-tuning an LLM          | Insufficient labeled data; overkill for current scope.                 |
| OpenSearch Hybrid Index     | Adds infra overhead; Cloud Run’s stateless model favored local Chroma. |
| Knowledge Graph Integration | Needs structured member relations not available in raw text.           |
| Simple Keyword Search Only  | Poor recall and reasoning accuracy on paraphrased queries.             |

The final pipeline balances **accuracy, transparency, and efficiency**, while remaining lightweight enough to run fully within a Cloud Run container.

---






