"""
AI Teacher - Backend Server
"""

import os
import json
import re
import traceback
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from google import genai
from google.genai import types
from passlib.context import CryptContext

from backend.rag_system import (
    add_document,
    retrieve_relevant_chunks,
    list_document_ids
)

from backend.tts_gemini import generate_narration_audio
from backend.simli_client import (
    generate_video as simli_generate_video,
    PRESET_FACES
)
from backend.visual_generator import generate_visual

# MongoDB
from database.database import db


# =====================================================================
# ENVIRONMENT
# =====================================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = None

if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)

MODEL_NAME = "gemini-3.6-flash"


# =====================================================================
# FASTAPI
# =====================================================================

app = FastAPI(
    title="AI Teacher Backend"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =====================================================================
# GLOBAL ERROR HANDLER
# =====================================================================

@app.exception_handler(Exception)
async def global_exception_handler(
    request: Request,
    exc: Exception
):
    traceback.print_exc()

    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Unhandled error: {type(exc).__name__}: {str(exc)}"
        }
    )


# =====================================================================
# HEALTH CHECK
# =====================================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "model": MODEL_NAME
    }


# =====================================================================
# REQUEST MODELS
# =====================================================================

class LessonRequest(BaseModel):
    topic: str
    level: str = "beginner"
    time_minutes: int = 20
    language: str = "English"
    document_id: str = None


class QuizRequest(BaseModel):
    topic: str
    lesson_summary: str
    num_questions: int = 3


class ChatRequest(BaseModel):
    topic: str
    message: str
    document_id: str = None


class AuthRequest(BaseModel):
    name: str
    email: str
    password: str


class QuizScoreRequest(BaseModel):
    user_id: str
    topic: str
    score: int
    total: int


# =====================================================================
# GEMINI JSON HELPER
# =====================================================================

def ask_gemini_for_json(prompt: str) -> dict:

    # ---------------------------------------------------------
    # LOCAL FALLBACK
    # ---------------------------------------------------------

    if client is None:

        match = re.search(r"Topic:\s*(.+)", prompt)

        topic = (
            match.group(1).strip()
            if match
            else "the requested topic"
        )

        return {
            "topic": topic,
            "level": "beginner",
            "language": "English",
            "scenes": [
                {
                    "scene_number": 1,
                    "narration": (
                        f"Let's begin by understanding {topic}. "
                        "We will learn the basic idea step by step."
                    ),
                    "visual_type": "text_slide",
                    "visual_description": (
                        f"Introduction to {topic} with the key idea highlighted."
                    ),
                    "checkpoint_question": (
                        f"What is the main idea behind {topic}?"
                    )
                },
                {
                    "scene_number": 2,
                    "narration": (
                        f"Now let's break {topic} into its most "
                        "important concepts."
                    ),
                    "visual_type": "diagram",
                    "visual_description": (
                        f"A simple concept diagram showing the main "
                        f"components of {topic}."
                    ),
                    "checkpoint_question": (
                        f"Can you name one important component of {topic}?"
                    )
                },
                {
                    "scene_number": 3,
                    "narration": (
                        f"Let's look at how {topic} works in practice. "
                        "A practical example helps connect theory with reality."
                    ),
                    "visual_type": "example",
                    "visual_description": (
                        f"A practical real-world example demonstrating {topic}."
                    ),
                    "checkpoint_question": (
                        f"Where could you apply {topic} in a real-world situation?"
                    )
                },
                {
                    "scene_number": 4,
                    "narration": (
                        f"Finally, let's summarize {topic}. "
                        "Remember the definition, key concepts, "
                        "and how they work together."
                    ),
                    "visual_type": "text_slide",
                    "visual_description": (
                        f"A summary slide containing the key points of {topic}."
                    ),
                    "checkpoint_question": (
                        f"How would you explain {topic} to a friend?"
                    )
                }
            ]
        }

    # ---------------------------------------------------------
    # GEMINI
    # ---------------------------------------------------------

    try:

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.7,
            ),
        )

    except Exception as e:

        raise HTTPException(
            status_code=502,
            detail=f"Gemini API call failed: {type(e).__name__}: {str(e)}"
        )

    try:

        if not response.candidates:

            feedback = getattr(
                response,
                "prompt_feedback",
                None
            )

            raise HTTPException(
                status_code=502,
                detail=(
                    "Gemini returned no candidates. "
                    f"Prompt feedback: {feedback}"
                )
            )

        text = response.text

        if not text:

            raise HTTPException(
                status_code=502,
                detail="Gemini returned an empty response."
            )

        return json.loads(text)

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=502,
            detail=(
                "Could not parse Gemini response: "
                f"{type(e).__name__}: {str(e)}"
            )
        )


# =====================================================================
# AI LESSON PLANNER
# =====================================================================

@app.post("/plan-lesson")
def plan_lesson(req: LessonRequest):

    context = ""

    if req.document_id:

        try:

            chunks = retrieve_relevant_chunks(
                document_id=req.document_id,
                query=req.topic,
                n_results=5
            )

            if chunks:
                context = "\n\n".join(
                    str(chunk)
                    for chunk in chunks
                )

        except Exception as e:

            print("RAG retrieval warning:", e)

    prompt = f"""
Create a beginner-friendly AI Teacher lesson.

Topic: {req.topic}

Level: {req.level}

Language: {req.language}

Time: {req.time_minutes} minutes

Study material retrieved from the user's document:

{context}

Create a lesson with 4 scenes.

Each scene must contain:

- scene_number
- narration
- visual_type
- visual_description
- checkpoint_question

Return ONLY valid JSON.
"""

    return ask_gemini_for_json(prompt)


# =====================================================================
# QUIZ
# =====================================================================

@app.post("/generate-quiz")
def generate_quiz(req: QuizRequest):

    questions = [

        {
            "question": f"What is the main idea of {req.topic}?",
            "options": [
                f"Understanding the fundamental concepts of {req.topic}",
                "Deleting all data",
                "Turning off the computer",
                "None of these"
            ],
            "answer": (
                f"Understanding the fundamental concepts of {req.topic}"
            )
        },

        {
            "question": f"Why is it important to learn {req.topic}?",
            "options": [
                "It helps understand and apply the concept",
                "It makes the computer slower",
                "It removes the operating system",
                "It has no practical use"
            ],
            "answer": "It helps understand and apply the concept"
        },

        {
            "question": (
                f"Which approach is best when studying {req.topic}?"
            ),
            "options": [
                "Understand the concept and practice it",
                "Memorize everything without understanding",
                "Skip the examples",
                "Avoid asking questions"
            ],
            "answer": "Understand the concept and practice it"
        }

    ]

    return {
        "topic": req.topic,
        "questions": questions[:req.num_questions]
    }


# =====================================================================
# AI TEACHER CHAT
# =====================================================================

@app.post("/chat")
def teacher_chat(req: ChatRequest):

    context = ""

    if req.document_id:

        try:

            chunks = retrieve_relevant_chunks(
                document_id=req.document_id,
                query=req.message,
                n_results=5
            )

            if chunks:
                context = "\n\n".join(
                    str(chunk)
                    for chunk in chunks
                )

        except Exception as e:

            print("Chat RAG warning:", e)

    # Gemini available
    if client is not None:

        prompt = f"""
You are a friendly AI Teacher.

Topic:
{req.topic}

Study material:
{context}

Student question:
{req.message}

Explain the answer clearly and simply.

Use examples when useful.

If the study material does not contain the answer,
say so honestly.

Answer the student directly.
"""

        try:

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )

            return {
                "reply": response.text
            }

        except Exception as e:

            print("Gemini chat error:", e)

    # Local fallback
    return {
        "reply": (
            f"I understand your question about {req.topic}. "
            f'Your question was: "{req.message}". '
            "Once the AI model is connected, I will give you "
            "a detailed explanation based on your study material."
        )
    }


# =====================================================================
# AUTHENTICATION
# =====================================================================

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


@app.post("/signup")
def signup(req: AuthRequest):

    users = db["users"]

    existing_user = users.find_one({
        "email": req.email
    })

    if existing_user:

        raise HTTPException(
            status_code=400,
            detail="User already exists"
        )

    user = {
        "name": req.name,
        "email": req.email,
        "password": pwd_context.hash(req.password),
        "created_at": datetime.utcnow()
    }

    result = users.insert_one(user)

    return {
        "success": True,
        "user_id": str(result.inserted_id),
        "name": req.name,
        "email": req.email
    }


@app.post("/login")
def login(req: AuthRequest):

    users = db["users"]

    user = users.find_one({
        "email": req.email
    })

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not pwd_context.verify(
        req.password,
        user["password"]
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    return {
        "success": True,
        "user_id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"]
    }


# =====================================================================
# QUIZ SCORE
# =====================================================================

@app.post("/quiz-score")
def save_quiz_score(req: QuizScoreRequest):

    percentage = (
        round((req.score / req.total) * 100)
        if req.total
        else 0
    )

    db["quiz_scores"].insert_one({

        "user_id": req.user_id,

        "topic": req.topic,

        "score": req.score,

        "total": req.total,

        "percentage": percentage,

        "created_at": datetime.utcnow()
    })

    return {
        "success": True,
        "percentage": percentage
    }

# ---------------------------------------------------------------------
# DOCUMENT UPLOAD + RAG
# ---------------------------------------------------------------------

from fastapi import UploadFile, File, Form
from backend.rag_system import add_document, list_document_ids


@app.post("/upload-document")
def upload_document(
    file: UploadFile = File(...),
    document_id: str = Form(...)
):
    os.makedirs("uploaded_documents", exist_ok=True)

    save_path = f"uploaded_documents/{file.filename}"

    with open(save_path, "wb") as f:
        f.write(file.file.read())

    try:
        chunk_count = add_document(save_path, document_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "document_id": document_id,
        "filename": file.filename,
        "chunks_stored": chunk_count,
        "message": "Document processed successfully."
    }


@app.get("/list-documents")
def list_documents():
    return {
        "document_ids": list_document_ids()
    }