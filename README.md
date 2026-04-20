# SmartStudy AI

SmartStudy AI is a multi-tool learning platform built for the **Gemma 4 Good Hackathon**.

It combines local **Gemma via Ollama**, **LightRAG** for grounded document retrieval, lightweight **fine-tuning pipelines**, and **Obsidian-compatible export** into a single Streamlit product for students, self-learners, and knowledge workers.

Quick links:

- `HACKATHON_SUBMISSION.md`: judge-facing summary
- `PROJECT_STATUS.md`: what is working and what is left
- `fine_tuning/README.md`: open-source training path
- `fine_tuning/RUNBOOK.md`: exact training and deployment run order
- `assets/demo_inputs/README.md`: repeatable demo inputs
- `DEMO_SCRIPT.md`: 3-minute and 5-minute presentation flow
- `DEMO_SCRIPT_3_MIN_WORD_FOR_WORD.md`: exact spoken demo script
- `JUDGE_CHECKLIST.md`: pre-demo checklist
- `PITCH_60_SECONDS.md`: short spoken pitch
- `DEVPOST_SUBMISSION.md`: ready-to-edit submission draft
- `TOOL_FINE_TUNING_BLUEPRINT.md`: best fine-tuning method per tool
- `ADVERSARIAL_AUDIT.md`: debug hardening and fixes applied

## Why This Project

Modern learners are overloaded with PDFs, lecture notes, videos, podcasts, and fragmented study material. SmartStudy AI turns those raw inputs into usable learning artifacts:

- grounded document Q&A
- adaptive quizzes
- study guides and plans
- multi-source synthesis
- research briefs with web sources
- code and architecture analysis tools

The project is designed around a practical idea:

- use **RAG** when answers must be grounded in source material
- use **CAG** when the full context is already available and speed matters
- use **Gemma-first local inference** to keep the workflow accessible and affordable

## Core Capabilities

### Module A: Study Tools
- `NeuroRead`: document Q&A with LightRAG
- `QuizVerse`: quiz generation from pasted text or PDFs
- `PrepMaster`: week-by-week study plans
- `EduTube`: YouTube transcript to study notes / flashcards
- `MindMapper`: Mermaid concept maps
- `NetSeek`: web research with source-aware synthesis
- `GraphiQ`: chart/code generation assistant
- `WriteWise`: writing assistant
- `CodeBuddy`: code explanation/debug/review helper
- `DSASage`: data structures and algorithms tutor
- `PaperAnalyzer`: arXiv search, paper analysis, grounded Q&A

### Module B: NotebookLM-style Tools
- `AudioOverview`: transcript analysis + optional MP3 narration
- `Studio`: flashcards, summaries, study guides from one source
- `MultiSourceSynth`: source-aware multi-document synthesis

### Module C: Idea Tools
- `IdeaSpark`: brainstorm and expand ideas
- `FeatureForge`: product specs, user stories, API ideas

### Module D: CodeLens
- `CodeFlow`: code-to-flowchart diagrams
- `ArchViz`: architecture diagram generator
- `LogicTrace`: debug analysis, execution traces, triage plans
- `DocGen`: documentation and README generation

## Architecture

### Inference
- **Gemma via Ollama** for the majority of generation flows
- **LightRAG** for grounded document retrieval and graph-backed question answering
- **Local `rag_engine.py` fallback** for standalone retrieval workflows
- **`vision_engine.py`** for multimodal document-page analysis when a vision-capable Gemma/Ollama model is available

### Generation Strategies
- **RAG**: NeuroRead, PaperAnalyzer, document-grounded workflows
- **CAG**: QuizVerse, Studio, PrepMaster, AudioOverview, EduTube

### Export Layer
- all major outputs can be exported into `data/obsidian_vault/`
- Mermaid diagrams are preserved in Obsidian-compatible markdown

### Structured Output Layer
- `function_calling.py` defines reusable JSON schemas for quizzes, flashcards, study plans, and citation-oriented outputs

### Fine-Tuning Pipeline
The repo also includes a staged fine-tuning workflow under `fine_tuning/`:

- Stage 1: SFT + rsLoRA
- Stage 2: GRPO
- Stage 3: SimPO
- Evaluation + GGUF export for local deployment

There is also a context-followup dataset generator in `fine_tuning/prepare_context_qa_dataset.py` for improving grounded conversational behavior.

## Tech Stack

- Python
- Streamlit
- Ollama
- Gemma 4
- LightRAG
- Anthropic SDK (available for optional Claude-backed workflows)
- Plotly
- `youtube-transcript-api`
- `duckduckgo-search`
- `gTTS`
- `pypdf`

## Repository Structure

```text
SmartstudyAI/
├── main.py
├── pages/
├── core/
├── fine_tuning/
├── data/
├── LightRAG/
├── requirements.txt
└── README.md
```

## Setup

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Prepare environment

Create a `.env` file from `.env.example`.

```env
ANTHROPIC_API_KEY=your_key_here
OLLAMA_HOST=http://localhost:11434
LIGHTRAG_HOST=http://localhost:9621
```

### 3. Start Ollama

Make sure Ollama is running and a Gemma model is available.

```bash
ollama serve
ollama pull gemma4:e2b
```

Use any local Gemma model name you actually have available in Ollama.

### 4. Start LightRAG

LightRAG is vendored in this repository. Start the API server separately.

Example:

```bash
cd LightRAG
lightrag-server --llm-binding ollama --embedding-binding ollama
```

### 5. Run the app

```bash
./run.sh
```

For a more complete judge setup that attempts to start LightRAG automatically:

```bash
./judge_demo.sh
```

Or:

```bash
streamlit run main.py
```

## Demo Flow

For a strong demo, the recommended sequence is:

1. `NetSeek`
   show live web research with visible source links
2. `EduTube`
   load a YouTube transcript and generate notes / flashcards
3. `NeuroRead`
   upload documents and ask grounded questions with references
4. `QuizVerse`
   generate an interactive quiz from study material
5. `AudioOverview`
   generate a podcast-style summary and export MP3 narration
6. `MultiSourceSynth`
   combine multiple sources into a cited synthesis
7. `CodeFlow` / `ArchViz` / `LogicTrace`
   show the platform also supports technical learners and builders

For a shorter judge version, run:

1. `NetSeek`
2. `EduTube`
3. `NeuroRead`
4. `QuizVerse`
5. `AudioOverview`

For exact page-by-page prompts and inputs, see `assets/demo_inputs/page_by_page_demo.md`.

## Screenshots

Add final screenshots under `assets/screenshots/` and reference them here before submission.

Suggested images:

- `assets/screenshots/homepage.png`
- `assets/screenshots/netseek.png`
- `assets/screenshots/neuroread.png`
- `assets/screenshots/quizverse.png`
- `assets/screenshots/audiooverview.png`
- `assets/screenshots/logictrace.png`

Markdown blocks to use once the images are captured:

```md
![SmartStudy AI Homepage](assets/screenshots/homepage.png)

![NetSeek Web Research](assets/screenshots/netseek.png)

![NeuroRead Grounded Q&A](assets/screenshots/neuroread.png)

![QuizVerse Quiz Results](assets/screenshots/quizverse.png)

![AudioOverview Narration](assets/screenshots/audiooverview.png)

![LogicTrace Debug Analysis](assets/screenshots/logictrace.png)
```

## What Makes This Submission Strong

- **Real product breadth**: not a single demo, but a platform with multiple integrated tools
- **Grounded answers**: LightRAG-backed retrieval for document workflows
- **Local-first**: Gemma via Ollama keeps the core experience accessible
- **Practical outputs**: quizzes, plans, diagrams, flashcards, notes, exports
- **Submission depth**: includes both runtime product and fine-tuning pipeline

## Submission Notes

See `HACKATHON_SUBMISSION.md` for the concise pitch, `PROJECT_STATUS.md` for the engineering status snapshot, and `fine_tuning/README.md` for the open-source training path.

## Current Maturity

This project is a polished hackathon prototype, not yet a production SaaS.

Strengths:
- broad feature coverage
- coherent multipage app
- local inference support
- source-aware research and RAG workflows

Known limitations:
- LightRAG still depends on a separately running server
- some advanced pages are still prompt-driven rather than deeply tool-integrated
- fine-tuning scripts are included, but dataset assets must be prepared before training

## Future Work

- deeper citation rendering and source snippets in all RAG pages
- stronger evaluation for fine-tuned Gemma checkpoints
- session history and notebook-style source collections
- richer visualizations and analytics for learning progress
- packaged deployment for easier judging/demo setup

## License

Currently unlicensed unless you add a project license.
