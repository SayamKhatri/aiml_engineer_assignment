from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional


class Metadata(BaseModel):
    user_name: Optional[str] = Field(None, description="Full Name or null if not mentioned")
    category: List[str] = Field(
        description="One or more categories (max 2) from the predefined list that the query may relate to"
    )


parser = PydanticOutputParser(pydantic_object=Metadata)

prompt = ChatPromptTemplate.from_template("""
You are a precise and reasoning-based information extractor.

Your task:
1. Identify the user_name mentioned in the query (if any).
2. Classify the query into up to two of the following 5 categories, ordered by relevance:
   - Travel & Accommodation: hotels, flights, villas, itineraries, trip bookings, or travel arrangements.
   - Dining & Experiences: restaurant bookings, dietary or allergy requests, concerts, cultural or social events, entertainment, or art-related experiences.
   - Personal & Wellness: spa, health, beauty, gifting, security, personal trainers, or wellness-related needs.
   - Account & Finance: payments, invoices, refunds, credit cards, or profile/contact updates.
   - Transport & Mobility: cars, drivers, chauffeurs, limousines, or other ground transport not part of a larger travel booking.

Classification Rules:
- Always return a list containing one or two categories.
- The first category must be the one most directly related to the query (explicit meaning).
- The second category, if applicable, should reflect a logical or contextual relationship that can be inferred from the situation.
  - Example: "What are Vikram's dietary allergies?" -> ["Dining & Experiences", "Personal & Wellness"]
  - Example: "What are Lorenzo's pillow preferences?" -> ["Personal & Wellness", "Travel & Accommodation"]
- If no secondary category makes sense, return only one.
- Do not add reasoning text - return only JSON.

Return a JSON object that strictly follows this format:
{format_instructions}

Query: {query}
""")

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0
)


def extract_metadata(query: str):
    formatted_prompt = prompt.format_messages(
        query=query,
        format_instructions=parser.get_format_instructions()
    )
    response = llm.invoke(formatted_prompt)

    try:
        parsed = parser.parse(response.content)

        if isinstance(parsed.category, str):
            parsed.category = [parsed.category]
        elif parsed.category is None:
            parsed.category = []

        return parsed

    except Exception as e:
        return Metadata(user_name=None, category=[])

