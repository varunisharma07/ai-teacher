"""
RAG (Retrieval-Augmented Generation) system.
------------------------------------------------
This is what lets the AI Teacher actually learn from an uploaded
document instead of just guessing from general knowledge. In plain
words, here's the whole idea:

1. Take an uploaded file (PDF/DOCX/PPTX) and pull out all its text.
2. Chop that text into small chunks (a few paragraphs each) - this is
   called "chunking". Small chunks are easier to search accurately.
3. Turn each chunk into a list of numbers that represents its meaning
   (an "embedding"), and store all of these in a small local database
   (Chroma) - this all happens automatically and locally, no API key
   or internet service needed for this part.
4. Later, when planning a lesson, we search that database for the
   chunks most relevant to the topic, and hand those chunks to Gemini
   as reference material - so it explains the ACTUAL uploaded content
   instead of making things up.

Chroma stores its database in a local folder called "chroma_db" (created
automatically next to this file) - this persists between runs, so you
don't need to re-upload documents every time you restart your server.
"""

import os
import chromadb
from pypdf import PdfReader
from docx import Document as DocxDocument
from pptx import Presentation

CHROMA_DB_PATH = "chroma_db"
COLLECTION_NAME = "lesson_materials"

_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
_collection = _client.get_or_create_collection(COLLECTION_NAME)


# ---------------------------------------------------------------------
# STEP 1: Extract raw text from whatever file type was uploaded.
# ---------------------------------------------------------------------
def extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    elif ext == ".docx":
        doc = DocxDocument(file_path)
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)

    elif ext == ".pptx":
        prs = Presentation(file_path)
        text_runs = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text:
                    text_runs.append(shape.text)
        return "\n".join(text_runs)

    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    else:
        raise ValueError(f"Unsupported file type: {ext}. Supported: .pdf, .docx, .pptx, .txt")


# ---------------------------------------------------------------------
# STEP 2: Split the text into overlapping chunks.
# "Overlap" means each chunk shares a bit of text with the next one,
# so we don't accidentally cut a concept in half between two chunks.
# ---------------------------------------------------------------------
def chunk_text(text: str, chunk_size: int = 200, overlap: int = 40) -> list:
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap  # step forward, but re-include the overlap

    return chunks


# ---------------------------------------------------------------------
# STEP 3: Process an uploaded file and store its chunks in Chroma.
# ---------------------------------------------------------------------
def add_document(file_path: str, document_id: str) -> int:
    """
    file_path: path to the uploaded file on disk
    document_id: a unique name for this document (e.g. "chapter4_physics")
                 - used later to search only within this specific document
    Returns: the number of chunks that were stored
    """
    text = extract_text(file_path)
    chunks = chunk_text(text)

    if not chunks:
        raise ValueError("No text could be extracted from this file.")

    ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"document_id": document_id, "chunk_index": i} for i in range(len(chunks))]

    _collection.add(ids=ids, documents=chunks, metadatas=metadatas)
    return len(chunks)


# ---------------------------------------------------------------------
# STEP 4: Retrieve the chunks most relevant to a topic/question, from
# ONE specific uploaded document.
# ---------------------------------------------------------------------
def retrieve_relevant_chunks(document_id: str, query: str, n_results: int = 5) -> list:
    results = _collection.query(
        query_texts=[query],
        n_results=n_results,
        where={"document_id": document_id},
    )
    # results["documents"] is a list of lists (one list per query) - we
    # only sent one query, so we take the first (and only) inner list.
    return results["documents"][0] if results["documents"] else []


def list_document_ids() -> list:
    """Utility function - returns every document_id currently stored,
    useful for checking what's already been uploaded."""
    all_items = _collection.get()
    doc_ids = {meta["document_id"] for meta in all_items["metadatas"]}
    return sorted(doc_ids)
