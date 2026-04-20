# SmartStudy AI — Gemma 4 Good Hackathon Edition
## Complete Project Plan (A to Z)

---

## 1. PROJECT OVERVIEW

**What:** A comprehensive AI-powered educational platform that combines 16 tools across 4 modules, powered by fine-tuned Gemma 4, Claude API, RAG, and CAG — built for the Gemma 4 Good Hackathon (Education Track).

**Competition:** Gemma 4 Good Hackathon | Kaggle × Google DeepMind
**Prize Pool:** $200,000 + $10,000 Unsloth fine-tuning prize
**Deadline:** May 18, 2026, 23:59 UTC
**Track:** Future of Education

---

## 2. TECH STACK

### Core AI Models
| Model | Purpose | Where it runs |
|-------|---------|---------------|
| Gemma 4 E4B (fine-tuned) | Quiz generation, document comprehension, study artifacts | Kaggle notebook (T4 GPU) / Ollama local |
| Gemma 4 26B MoE | Research synthesis, mind mapping, audio script generation, idea generation | Kaggle notebook (P100/T4) |
| Claude API (Sonnet 4.6) | Code analysis, flowcharts, architecture diagrams, documentation | API calls from Streamlit |

### RAG vs CAG Strategy
| Technique | When to use | Implementation |
|-----------|-------------|----------------|
| **RAG** (Retrieval-Augmented Generation) | NeuroRead, NetSeek, Academic Paper Analyzer, Source Grounding — when answers must be cited and grounded in uploaded documents | FAISS vector store + sentence-transformers embeddings + Gemma 4 |
| **CAG** (Cache-Augmented Generation) | QuizVerse, Studio artifacts, PrepMaster — when speed matters and context is already loaded in the prompt | Preload full document text into Gemma 4's 256K context window, no retrieval step |

**Rule of thumb:** If the user asks a question about their documents → RAG (accuracy + citations). If the system is generating content FROM documents already in context → CAG (speed).

### Development Tools
| Tool | Purpose |
|------|---------|
| **Google Antigravity** | Primary IDE — use Manager View to dispatch agents for parallel feature development |
| **Claude (via Antigravity)** | Code generation, debugging, architecture planning inside the IDE |
| **OpenAI GPT-OSS (via Antigravity)** | Alternative model for code review and second opinions |
| **Kaggle Notebooks** | Fine-tuning Gemma 4, running demos, free T4/P100 GPU |
| **GitHub** | Public repo (required for submission) |

### Framework & Libraries
| Library | Version | Purpose |
|---------|---------|---------|
| `streamlit` | latest | Web UI framework |
| `unsloth` | latest | Gemma 4 fine-tuning (2x speed, 70% less VRAM) |
| `transformers` | ≥4.45 | Model loading & inference |
| `torch` | ≥2.4 | PyTorch backend |
| `sentence-transformers` | latest | Embedding generation for RAG |
| `faiss-cpu` | latest | Vector store for RAG retrieval |
| `anthropic` | latest | Claude API client |
| `trl` | latest | SFTTrainer for fine-tuning |
| `peft` | latest | LoRA adapter management |
| `datasets` | latest | HuggingFace dataset loading |
| `pymupdf` (fitz) | latest | PDF text extraction |
| `Pillow` | latest | Image processing |
| `bark` or `TTS` | latest | Text-to-speech for Audio Overview |
| `plotly` | latest | Interactive charts for GraphiQ |
| `streamlit-mermaid` | latest | Mermaid.js diagram rendering |
| `langchain` | latest | RAG pipeline orchestration |
| `ollama` | latest | Local model serving |

### Install Commands
```bash
# Core
pip install streamlit torch transformers accelerate

# Fine-tuning (Kaggle/Colab only)
pip install unsloth trl peft datasets bitsandbytes

# RAG pipeline
pip install faiss-cpu sentence-transformers langchain langchain-community

# Document processing
pip install pymupdf Pillow pytesseract pdf2image

# AI APIs
pip install anthropic ollama

# Audio (for Audio Overview)
pip install TTS bark scipy soundfile

# Visualization
pip install plotly streamlit-mermaid

# YouTube processing (for EduTube)
pip install youtube-transcript-api pytube

# Additional
pip install python-dotenv requests beautifulsoup4
```

---

## 3. PROJECT STRUCTURE

```
SmartStudy-Gemma4/
│
├── README.md                          # Technical write-up (submission requirement)
├── requirements.txt                   # All dependencies
├── .env.example                       # API key template
├── .gitignore
│
├── main.py                            # Streamlit app entry point + homepage
│
├── core/                              # Shared engines
│   ├── __init__.py
│   ├── gemma_engine.py                # Gemma 4 inference wrapper (Ollama + HF)
│   ├── claude_engine.py               # Claude API wrapper
│   ├── rag_engine.py                  # RAG: FAISS + embeddings + retrieval
│   ├── cag_engine.py                  # CAG: context preloading + fast generation
│   ├── vision_engine.py               # Gemma 4 vision: image → text
│   ├── tts_engine.py                  # Text-to-speech for Audio Overview
│   ├── function_calling.py            # Gemma 4 function calling schemas
│   └── utils.py                       # Shared utilities
│
├── pages/                             # Streamlit multi-page app
│   │
│   │── # --- MODULE A: Original SmartStudy Tools (Rebuilt on Gemma 4) ---
│   ├── 01_NetSeek.py                  # Research assistant (Gemma 4 + web search)
│   ├── 02_NeuroRead.py                # Document Q&A (Gemma 4 vision + RAG)
│   ├── 03_QuizVerse.py                # Adaptive quiz gen (fine-tuned Gemma 4 + CAG)
│   ├── 04_EduTube.py                  # YouTube → study materials (Gemma 4 26B)
│   ├── 05_MindMapper.py               # Concept maps (Gemma 4 → Mermaid.js)
│   ├── 06_PrepMaster.py               # Study plan generator (Gemma 4 + CAG)
│   ├── 07_GraphiQ.py                  # Math assistant (KEPT AS-IS — Desmos)
│   ├── 08_WriteWise.py                # Writing mentor (Gemma 4 26B)
│   ├── 09_CodeBuddy.py                # Coding assistant (Gemma 4 26B)
│   ├── 10_DSASage.py                  # DSA tutor (fine-tuned Gemma 4 + CAG)
│   ├── 11_PaperAnalyzer.py            # Academic paper analysis (Gemma 4 + RAG)
│   │
│   │── # --- MODULE B: NotebookLM-Style Features ---
│   ├── 12_AudioOverview.py            # Podcast-style deep dives (Gemma 4 + TTS)
│   ├── 13_Studio.py                   # One-click study artifacts (flashcards, guides)
│   ├── 14_MultiSourceSynth.py         # Cross-source analysis (Gemma 4 256K)
│   │
│   │── # --- MODULE C: Idea & Feature Generation ---
│   ├── 15_IdeaSpark.py                # Brainstorming engine (Gemma 4 reasoning)
│   ├── 16_FeatureForge.py             # Product feature generator (Gemma 4)
│   │
│   │── # --- MODULE D: CodeLens Suite (Claude API) ---
│   ├── 17_CodeFlow.py                 # Codebase → flowcharts (Claude → Mermaid.js)
│   ├── 18_ArchViz.py                  # Architecture diagrams (Claude → C4 model)
│   ├── 19_LogicTrace.py               # Debug visualizer (Claude)
│   └── 20_DocGen.py                   # Auto-documentation (Claude)
│
├── fine_tuning/                       # Fine-tuning pipeline
│   ├── prepare_dataset.py             # Dataset curation script
│   ├── train_eduquiz_lora.py          # EduQuiz LoRA training
│   ├── train_docread_lora.py          # DocRead vision LoRA training
│   ├── evaluate.py                    # Before/after comparison
│   ├── export_gguf.py                 # Export to GGUF for Ollama
│   └── datasets/
│       ├── eduquiz_train.jsonl        # Quiz generation training data
│       ├── eduquiz_eval.jsonl          # Quiz generation eval data
│       ├── docread_train.jsonl         # Document comprehension training data
│       └── docread_eval.jsonl          # Document comprehension eval data
│
├── data/                              # User uploads & vector stores
│   ├── uploads/                       # User-uploaded documents
│   ├── faiss_index/                   # FAISS vector store
│   └── audio_cache/                   # Generated audio files
│
├── assets/                            # Static assets
│   ├── logo.png
│   └── demo_screenshots/
│
├── notebooks/                         # Kaggle submission notebooks
│   ├── gemma4_finetune.ipynb          # Fine-tuning notebook
│   ├── gemma4_demo.ipynb              # Demo notebook
│   └── gemma4_eval.ipynb              # Evaluation notebook
│
└── demo_video/                        # Screen recordings for submission
    └── smartstudy_demo.mp4
```

---

## 4. FINE-TUNING PLAN

### LoRA Adapter 1: EduQuiz (quiz & study material generation)

**Goal:** Make Gemma 4 E4B consistently output structured JSON for quizzes, flashcards, and study guides at the correct difficulty level.

**Dataset sources:**
- SciQ (13,679 science exam questions) — `allenai/sciq` on HuggingFace
- ARC (7,787 grade-school science) — `allenai/ai2_arc`
- OpenBookQA (5,957 questions) — `allenai/openbookqa`
- MMLU subset (humanities + social sciences) — `cais/mmlu`
- Self-generated: prompt base Gemma 4 to create quiz JSON, manually curate best 500

**Target dataset size:** 5,000 examples
**Format:**
```json
{"messages": [
  {"role": "user", "content": "Generate 3 MCQ questions about [topic] for [grade level]. Output valid JSON: {questions: [{question, options: [4], correct_answer, explanation}]}"},
  {"role": "model", "content": "{\"questions\": [...]}"}
]}
```

**Training config:**
- Model: `unsloth/gemma-4-E4B-it`
- LoRA rank: 16
- LoRA alpha: 32
- Learning rate: 2e-4
- Epochs: 3
- Batch size: 2 (gradient accumulation: 4)
- Max seq length: 2048
- Quantization: 4-bit QLoRA
- Hardware: Kaggle T4 GPU (free)
- Estimated time: ~2-3 hours

### LoRA Adapter 2: DocRead (multimodal document comprehension)

**Goal:** Improve Gemma 4 E4B's ability to read photographed textbooks, handwritten notes, and extract structured information.

**Dataset sources:**
- DocVQA (12,000+ document visual Q&A pairs) — `lmms-lab/DocVQA`
- ChartQA (chart understanding) — subset
- InfographicVQA — subset
- Self-created: photograph 50 textbook pages, create Q&A pairs manually

**Target dataset size:** 3,000 examples (vision fine-tuning needs fewer examples)
**Training:** Same config as above but with `finetune_vision_layers=True`

### Evaluation plan
- Hold out 200 examples per adapter
- Metrics: JSON format compliance rate, answer accuracy, BLEU score for explanations
- Run base model vs fine-tuned model on same test set
- Document improvement in technical write-up

---

## 5. RAG PIPELINE ARCHITECTURE

```
User uploads document(s)
        │
        ▼
   PDF/Image → Text extraction (PyMuPDF / Gemma 4 vision for images)
        │
        ▼
   Text → Chunks (500 tokens, 50 token overlap)
        │
        ▼
   Chunks → Embeddings (sentence-transformers/all-MiniLM-L6-v2)
        │
        ▼
   Embeddings → FAISS vector store (saved locally)
        │
        ▼
   User asks question
        │
        ▼
   Question → Embedding → FAISS top-k retrieval (k=5)
        │
        ▼
   Retrieved chunks + question → Gemma 4 prompt
        │
        ▼
   Gemma 4 generates answer WITH inline citations [Source 1, p.23]
```

**Used by:** NeuroRead, NetSeek, Academic Paper Analyzer, Source Grounding, Multi-Source Synthesis

---

## 6. CAG PIPELINE ARCHITECTURE

```
User selects document(s) already in session
        │
        ▼
   Full document text preloaded into Gemma 4 context window (up to 256K tokens)
        │
        ▼
   User requests: "Generate quiz" / "Create flashcards" / "Make study plan"
        │
        ▼
   Gemma 4 (fine-tuned) processes full context + function calling schema
        │
        ▼
   Structured JSON output → rendered as interactive UI component
```

**Used by:** QuizVerse, Studio, PrepMaster, DSA Sage
**Why CAG here:** No retrieval step needed — the model already has the full document. Speed is 2-3x faster than RAG for generation tasks.

---

## 7. TASK BREAKDOWN (PROJECT MANAGER VIEW)

### PHASE 0: Setup (Day 1)
| # | Task | Time | Priority |
|---|------|------|----------|
| 0.1 | Install Antigravity IDE | 15 min | P0 |
| 0.2 | Create GitHub repo `SmartStudy-Gemma4` | 10 min | P0 |
| 0.3 | Fork AdityaButani/SmartStudy-AI, study codebase | 1 hr | P0 |
| 0.4 | Create Kaggle account, join hackathon | 10 min | P0 |
| 0.5 | Set up `.env` with Claude API key | 10 min | P0 |
| 0.6 | Install all dependencies (see install commands above) | 20 min | P0 |
| 0.7 | Set up Ollama locally + pull `gemma4:e4b` | 30 min | P0 |
| 0.8 | Create project structure (folders + empty files) | 30 min | P0 |

### PHASE 1: Core Engines (Days 2-3)
| # | Task | Time | Priority |
|---|------|------|----------|
| 1.1 | Build `gemma_engine.py` — Ollama + HF inference wrapper | 2 hr | P0 |
| 1.2 | Build `claude_engine.py` — Claude API wrapper | 1 hr | P0 |
| 1.3 | Build `rag_engine.py` — FAISS + embeddings + retrieval | 3 hr | P0 |
| 1.4 | Build `cag_engine.py` — context preloading + fast gen | 2 hr | P0 |
| 1.5 | Build `vision_engine.py` — image → text via Gemma 4 | 2 hr | P0 |
| 1.6 | Build `function_calling.py` — JSON schemas for structured output | 2 hr | P0 |
| 1.7 | Build `main.py` — homepage with navigation | 1 hr | P0 |
| 1.8 | Test all engines with basic prompts | 1 hr | P0 |

### PHASE 2: Fine-Tuning (Days 4-5)
| # | Task | Time | Priority |
|---|------|------|----------|
| 2.1 | Curate EduQuiz dataset (5,000 examples) | 4 hr | P0 |
| 2.2 | Curate DocRead dataset (3,000 examples) | 3 hr | P0 |
| 2.3 | Write `train_eduquiz_lora.py` with Unsloth | 2 hr | P0 |
| 2.4 | Run EduQuiz fine-tuning on Kaggle (T4 GPU) | 3 hr (training) | P0 |
| 2.5 | Write `train_docread_lora.py` with Unsloth | 2 hr | P0 |
| 2.6 | Run DocRead fine-tuning on Kaggle | 3 hr (training) | P0 |
| 2.7 | Run evaluation: base vs fine-tuned | 2 hr | P0 |
| 2.8 | Export to GGUF for Ollama deployment | 1 hr | P0 |
| 2.9 | Push fine-tuned model to HuggingFace Hub | 30 min | P1 |

### PHASE 3: Module A — SmartStudy Tools (Days 6-10)
| # | Task | Time | Priority |
|---|------|------|----------|
| 3.1 | Build NeuroRead (RAG + vision) | 4 hr | P0 |
| 3.2 | Build QuizVerse (fine-tuned + CAG + adaptive) | 4 hr | P0 |
| 3.3 | Build PrepMaster (CAG + study plan gen) | 3 hr | P0 |
| 3.4 | Build EduTube (YouTube transcript + Gemma 4) | 3 hr | P1 |
| 3.5 | Build MindMapper (Gemma 4 → Mermaid.js) | 3 hr | P1 |
| 3.6 | Build NetSeek (Gemma 4 + web search) | 3 hr | P1 |
| 3.7 | Port GraphiQ AS-IS (Desmos integration) | 1 hr | P1 |
| 3.8 | Build WriteWise (Gemma 4 writing mentor) | 2 hr | P2 |
| 3.9 | Build CodeBuddy (Gemma 4 coding assistant) | 2 hr | P2 |
| 3.10 | Build DSA Sage (fine-tuned + CAG) | 3 hr | P2 |
| 3.11 | Build Paper Analyzer (RAG) | 3 hr | P2 |

### PHASE 4: Module B — NotebookLM Features (Days 11-13)
| # | Task | Time | Priority |
|---|------|------|----------|
| 4.1 | Build Audio Overview (script gen + TTS) | 5 hr | P1 |
| 4.2 | Build Studio (one-click artifacts) | 3 hr | P0 |
| 4.3 | Build Multi-Source Synthesis (256K context) | 3 hr | P1 |
| 4.4 | Build source grounding with inline citations | 3 hr | P0 |

### PHASE 5: Module C — Idea Generation (Days 13-14)
| # | Task | Time | Priority |
|---|------|------|----------|
| 5.1 | Build IdeaSpark (SCAMPER, HMW, problem trees) | 3 hr | P1 |
| 5.2 | Build FeatureForge (feature suggestions + Kanban) | 3 hr | P2 |

### PHASE 6: Module D — CodeLens / Claude Suite (Days 14-16)
| # | Task | Time | Priority |
|---|------|------|----------|
| 6.1 | Build CodeFlow (Claude → flowcharts) | 4 hr | P1 |
| 6.2 | Build ArchViz (Claude → architecture diagrams) | 4 hr | P1 |
| 6.3 | Build LogicTrace (Claude → debug visualizer) | 3 hr | P2 |
| 6.4 | Build DocGen (Claude → auto-documentation) | 3 hr | P2 |

### PHASE 7: Polish & Submission (Days 17-18)
| # | Task | Time | Priority |
|---|------|------|----------|
| 7.1 | Write technical README (submission requirement) | 3 hr | P0 |
| 7.2 | Record demo video (all key features, offline demo) | 2 hr | P0 |
| 7.3 | Create Kaggle submission notebook | 2 hr | P0 |
| 7.4 | Push everything to public GitHub repo | 30 min | P0 |
| 7.5 | Submit on Kaggle before deadline | 30 min | P0 |
| 7.6 | Screenshot Kaggle submission for DSE evidence | 10 min | P0 |

---

## 8. PRIORITY MAP

If time is short, build ONLY these (Minimum Viable Submission):
1. ✅ `gemma_engine.py` + `rag_engine.py` + `cag_engine.py`
2. ✅ Fine-tuned EduQuiz LoRA adapter (Unsloth)
3. ✅ NeuroRead (document comprehension with RAG)
4. ✅ QuizVerse (adaptive quiz generation with CAG)
5. ✅ Studio (one-click flashcards/study guides)
6. ✅ CodeFlow (Claude → flowcharts)
7. ✅ README + demo video + Kaggle submission

Everything else is P1/P2 and adds strength but isn't required to submit.

---

## 9. ANTIGRAVITY WORKFLOW

### How to use Antigravity effectively for this project:

**Editor View** — for writing individual files (engines, pages)
**Manager View** — dispatch agents to build features in parallel:
- Agent 1: "Build the RAG engine in core/rag_engine.py using FAISS and sentence-transformers"
- Agent 2: "Build the QuizVerse page in pages/03_QuizVerse.py using the CAG engine"
- Agent 3: "Build the Claude wrapper in core/claude_engine.py"

**Model switching in Antigravity:**
- Use **Gemini 3 Pro** for fast scaffolding and boilerplate
- Use **Claude Sonnet 4.6** for complex logic, debugging, and code review
- Use **GPT-OSS** for second opinions on architecture decisions

**Knowledge base:** Save reusable prompts, function calling schemas, and code patterns to Antigravity's knowledge base so agents improve over time.

---

## 10. SUBMISSION CHECKLIST

| # | Requirement | Status |
|---|-------------|--------|
| 1 | Working demo (Kaggle notebook or deployed app) | ☐ |
| 2 | Public GitHub repo with all source code | ☐ |
| 3 | Technical write-up (README.md) | ☐ |
| 4 | Demo video showing real-world use | ☐ |
| 5 | Uses at least one Gemma 4 model | ☐ |
| 6 | Fine-tuned model (for Unsloth prize) | ☐ |
| 7 | Fine-tuned model pushed to HuggingFace Hub | ☐ |

### DSE Assignment Checklist (for INFO 511)
| # | Requirement | Status |
|---|-------------|--------|
| 1 | slide.pdf (one professional slide) | ☐ |
| 2 | reflection.qmd (600-1,000 words) | ☐ |
| 3 | evidence.pdf (Kaggle submission screenshot) | ☐ |

---

## 11. KEY PROMPTS & SCHEMAS

### Function calling schema for QuizVerse:
```json
{
  "name": "generate_quiz",
  "description": "Generate a structured quiz from educational content",
  "parameters": {
    "type": "object",
    "properties": {
      "questions": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "question": {"type": "string"},
            "type": {"type": "string", "enum": ["mcq", "true_false", "fill_blank"]},
            "options": {"type": "array", "items": {"type": "string"}},
            "correct_answer": {"type": "string"},
            "explanation": {"type": "string"},
            "difficulty": {"type": "string", "enum": ["easy", "medium", "hard"]},
            "bloom_level": {"type": "string", "enum": ["remember", "understand", "apply", "analyze", "evaluate", "create"]}
          }
        }
      }
    }
  }
}
```

### Claude prompt for CodeFlow:
```
You are a code architecture analyst. Given the following codebase, generate a Mermaid.js flowchart that shows:
1. The main execution flow
2. Function call relationships
3. Data flow between modules
4. External API calls

Output ONLY valid Mermaid.js syntax. Use clear, descriptive node labels.
Do not include any explanation outside the Mermaid code block.

Codebase:
{code}
```

---

## 12. TIMELINE SUMMARY

| Week | Focus | Key Deliverables |
|------|-------|-----------------|
| Week 1 (Apr 15-21) | Setup + Core Engines + Fine-tuning | Working engines, trained LoRA adapters |
| Week 2 (Apr 22-28) | Module A (SmartStudy tools) + Module B (NotebookLM) | 8-10 working tools |
| Week 3 (Apr 29-May 5) | Module C + D + Polish | IdeaSpark, CodeLens, demo video |
| Week 4 (May 6-12) | Testing, bug fixes, documentation | README, submission notebook |
| May 13-18 | Final submission + DSE deliverables | Kaggle submission, slide.pdf, reflection.qmd |

---

*Built for the Gemma 4 Good Hackathon | Kaggle × Google DeepMind | May 2026*
