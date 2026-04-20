"""NeuroRead — Document Q&A with context-augmented generation."""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel

from core.cag_engine import generate_from_context, generate_study_guide
from core.gemma_engine import GemmaConfig
from brahmavidya.memory import log_event, register_content

router = APIRouter()


def _extract_text(file_path: Path, filename: str) -> str:
    """Extract text from uploaded file."""
    suffix = Path(filename).suffix.lower()
    if suffix == ".txt":
        return file_path.read_text(errors="ignore")
    elif suffix == ".md":
        return file_path.read_text(errors="ignore")
    elif suffix == ".pdf":
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(str(file_path))
            text = "\n\n".join(page.get_text() for page in doc)
            doc.close()
            return text
        except ImportError:
            try:
                from PyPDF2 import PdfReader
                reader = PdfReader(str(file_path))
                return "\n\n".join(page.extract_text() or "" for page in reader.pages)
            except ImportError:
                return "[PDF extraction requires PyMuPDF or PyPDF2]"
    return file_path.read_text(errors="ignore")


class AskRequest(BaseModel):
    question: str
    context: str
    mode: str = "detailed"


class AskResponse(BaseModel):
    answer: str
    mode: str


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename or "doc.txt").suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    text = _extract_text(tmp_path, file.filename or "document")
    tmp_path.unlink(missing_ok=True)

    register_content("document", file.filename or "uploaded_doc", "NeuroRead",
                     char_count=len(text), file_type=Path(file.filename or "").suffix)
    log_event("NeuroRead", "content_ingested", file.filename or "document", source="document_upload")

    return {"text": text, "char_count": len(text), "filename": file.filename}


@router.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest):
    mode_instructions = {
        "concise": "Give a brief, focused answer in 2-3 sentences.",
        "detailed": "Give a thorough answer with explanations and examples from the text.",
        "study_guide": "Create a mini study guide section about this topic based on the text.",
    }

    instruction = f"""{req.question}

{mode_instructions.get(req.mode, mode_instructions['detailed'])}
Cite specific passages from the document when possible."""

    config = GemmaConfig(temperature=0.3)
    answer = generate_from_context(
        req.context, instruction,
        system_prompt="You are a knowledgeable tutor answering questions based on provided documents. Only use information from the given context.",
        config=config,
    )
    log_event("NeuroRead", "question_asked", req.question[:80], mode=req.mode)
    return AskResponse(answer=answer, mode=req.mode)


@router.post("/study-guide")
async def study_guide(context: str = Form(...)):
    config = GemmaConfig(temperature=0.4)
    guide = generate_study_guide(context, config=config)
    log_event("NeuroRead", "study_guide_generated", "Document study guide")
    return {"guide": guide}
