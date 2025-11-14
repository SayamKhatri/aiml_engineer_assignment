from dotenv import load_dotenv
from src.qa_service import QAService

load_dotenv()

# local testing

if __name__ == "__main__":
    service = QAService()
    
    user_query = "What do we know about Layla's spouse and family members?"
    answer = service.answer_question(user_query)
    
    print(f"\nQuestion: {user_query}")
    print(f"\nAnswer: {answer}\n")

