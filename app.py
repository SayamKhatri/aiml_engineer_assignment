from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.qa_service import QAService
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="QA Service", version="1.0.0")

qa_service = None


@app.on_event("startup")
async def startup_event():
    global qa_service
    try:
        qa_service = QAService()
    except Exception as e:
        print(f"Failed to initialize QA service: {e}")
        raise


class QuestionRequest(BaseModel):
    question: str


class AnswerResponse(BaseModel):
    answer: str


@app.get("/")
async def root():
    return {"status": "ok"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/question", response_model=AnswerResponse)
async def answer_question(request: QuestionRequest):
    if not qa_service:
        raise HTTPException(status_code=503, detail="Service not available")
    
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question is required")
    
    try:
        answer = qa_service.answer_question(request.question.strip())
        return AnswerResponse(answer=answer)
    except Exception as e:
        print(f"Error processing question: {e}")
        raise HTTPException(status_code=500, detail="Failed to process question")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
