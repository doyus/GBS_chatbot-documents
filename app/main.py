
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from core.rag_pipeline import DocumentQA
import os
import shutil

app = FastAPI()
qa_system = None

def get_qa_system():
    global qa_system
    if qa_system is None:
        qa_system = DocumentQA()
    return qa_system

# Permitir acceso desde frontend (Streamlit, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
async def root():
    return {
        "message": "Welcome to RAG Chatbot Documents API",
        "endpoints": {
            "upload": "/upload/ - Upload a PDF document",
            "ask": "/ask/ - Ask a question about uploaded documents",
            "docs": "/docs - Interactive API documentation"
        }
    }

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    qa = get_qa_system()
    qa.load_and_index_pdf(file_path)
    return {"message": "Document loaded and processed", "file": file.filename}

@app.post("/ask/")
async def ask_question(question: str = Form(...)):
    qa = get_qa_system()
    if not qa.qa_chain:
        index_loaded = qa.load_existing_index()
        if not index_loaded:
            return {"error": "No index loaded. Please upload a document first."}

    answer = qa.ask(question)
    return {"question": question, "answer": answer}
