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

## **Alternative Approaches and Iterative Improvements**


| **Iteration**                                    | **Approach Tried**                                                      | **Problem Identified**                                                           | **Improvement / Solution Implemented**                                              | **Key Outcome**                                       |
| ------------------------------------------------ | ----------------------------------------------------------------------- | -------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ----------------------------------------------------- |
| **1️⃣ Pure Vector Search**                       | Used Google Generative AI embeddings + ChromaDB for semantic retrieval. | Missed exact keyword matches (“diet” vs “dietary”), inconsistent user targeting. | Added lexical layer for precise keyword matching.                                   | Improved recall but still lacked precision.           |
| **2️⃣ Hybrid Search (BM25 + Vector)**            | Combined dense semantic retrieval with BM25 keyword scoring.            | Some queries retrieved irrelevant users or off-topic results.                    | Introduced user and category filters in query metadata.                             | Better factual grounding and relevance.               |
| **3️⃣ Name Resolution Layer**                    | Chroma filtering required exact matches (`user_name` mismatch).         | Queries like “Vikram D.” failed to match “Vikram Desai.”                         | Implemented fuzzy name resolution using RapidFuzz with canonical `user_index.json`. | Consistent, user-specific retrieval accuracy.         |
| **4️⃣ Category-Aware Filtering**                 | All messages stored together; semantic bleed between topics.            | Travel, dining, and wellness messages overlapped semantically.                   | Clustered messages (K-Means) + LLM labeling → consolidated 5 major categories.      | Retrieval now restricted to relevant category slices. |
| **5️⃣ Two-Category Reasoning Extraction**        | LLM sometimes picked only one narrow category.                          | Ambiguous queries (e.g., “dietary preferences”) span domains.                    | Modified extractor to return both *direct* and *reasoning-based* categories.        | Higher recall and cross-domain coverage.              

The final pipeline balances **accuracy, transparency, and efficiency**, while remaining lightweight enough to run fully within a Cloud Run container.

---

# **Data Insights**

Analysis of the member-message dataset reveals several data-quality issues and inconsistencies that impact how a natural-language QA system must be designed:

### **1. Mixed and Often Irrelevant Message Intent**

The dataset includes bookings, profile updates, complaints, preferences, confirmations, and many non-informative “thank you”, "I finally", or feedback messages. These conversational messages contain no actionable data and must be filtered to avoid polluting factual retrieval.

### **2. Ambiguous or Underspecified Requests**

Many requests lack essential information such as event names, venues, or locations (e.g., “four front-row seats for the game on November 20”). This creates ambiguity and requires the system to handle missing-context scenarios.

### **3. Preferences and Profile Data Embedded in Free-Form Text**

User preferences (“I prefer aisle seats”, “low-scent amenities”) and sensitive profile updates (phone numbers, credit-card suffixes, addresses, family contacts) appear inconsistently in unstructured text. These require careful extraction and normalization.

### **4. Redundant or Repeated Information**

Several users restate the same preferences or issues across multiple messages (e.g., repeated billing concerns or travel preferences). This redundancy requires consolidation to build consistent user profiles.










