# Tool Fine-Tuning Blueprint

This document converts the hackathon strategy into an implementation-facing blueprint.

It answers four questions for every tool:

1. What is the best model family for the task?
2. Does the tool actually need fine-tuning?
3. If yes, which method is best?
4. What is the current repo status versus the target design?

## Decision Rules

- Use **3-stage fine-tuning** only where the tool must produce consistent structured outputs, strong reasoning, and high pedagogical quality.
- Use **vision fine-tuning** only where document images, photographed notes, charts, or scanned PDFs are central to quality.
- Use **instruction LoRA** where format and domain tone matter, but RL-style optimization would be overkill.
- Use **prompting only** when the task is open-ended, creative, or already well served by a strong base model.
- Use **Claude** only for pages where code comprehension, long-form technical structure, or diagram fidelity materially outweigh local-first constraints.

## Master Assignment Table

| Tool | Best Model | Best Tuning Method | Stage | Inference Mode | Why |
|---|---|---|---|---|---|
| 01 NetSeek | Gemma 26B / strong Gemma local | No fine-tuning | None | Web search + RAG | Quality depends more on retrieval/source handling than adapter tuning |
| 02 NeuroRead | Gemma 4 multimodal + LightRAG | Vision LoRA + optional grounded QA SFT | Vision adapter + optional Stage 1 | RAG + Vision | Needs document/image understanding and grounded answers |
| 03 QuizVerse | Gemma 4 E4B | SFT + GRPO + SimPO | Stages 1-3 | CAG | Must output valid JSON, correct answers, explanations, Bloom tags |
| 04 EduTube | Gemma 26B | No fine-tuning | None | CAG (transcript) | Transcript-in-context is enough; retrieval matters less |
| 05 MindMapper | Gemma 26B | No fine-tuning | None | Prompting | Mermaid generation is prompt-structured, not domain-adapter limited |
| 06 PrepMaster | Gemma 4 E4B or 26B | Optional instruction LoRA | Optional Stage 1 only | CAG | Benefits from consistent study-plan structure but does not need RL |
| 07 GraphiQ | Gemma 26B | No fine-tuning | None | Prompting | Visualization code quality is prompt-sensitive, not worth custom tuning first |
| 08 WriteWise | Gemma 26B | No fine-tuning | None | Prompting | General writing quality already comes from base model capability |
| 09 CodeBuddy | Gemma 26B or Claude | No fine-tuning | None | Prompting | Better solved by stronger base reasoning than education-specific adapters |
| 10 DSASage | Gemma 4 E4B | SFT + GRPO + SimPO | Stages 1-3 | CAG (256K if available) | Needs stepwise reasoning, explanation quality, pedagogical control |
| 11 PaperAnalyzer | Gemma 4 multimodal + LightRAG | Vision LoRA + optional grounded QA SFT | Vision adapter + optional Stage 1 | RAG + Vision | Needs scanned-paper understanding, chart/table handling, grounded follow-up QA |
| 12 AudioOverview | Gemma 26B | No fine-tuning | None | CAG + TTS | Script quality is promptable; audio quality comes from TTS layer |
| 13 Studio | Gemma 4 E4B | SFT + GRPO + SimPO | Stages 1-3 | CAG | Central artifact generator; must be reliable across flashcards/guides/summaries |
| 14 MultiSourceSynth | Gemma 26B | No fine-tuning | None | CAG / long-context synthesis | Main challenge is long-context source handling, not adapter specialization |
| 15 IdeaSpark | Gemma 26B | No fine-tuning | None | Prompting | Creative breadth is better preserved without domain-constraining tuning |
| 16 FeatureForge | Gemma 26B | No fine-tuning | None | Prompting | Product/spec generation depends more on instruction quality than dataset tuning |
| 17 CodeFlow | Claude Sonnet / strongest code model | No fine-tuning in repo | N/A | Claude or top-tier code reasoning | Diagram fidelity and code path extraction favor stronger code-native reasoning |
| 18 ArchViz | Claude Sonnet / strongest code model | No fine-tuning in repo | N/A | Claude or top-tier code reasoning | Architecture diagrams benefit from stronger systems reasoning |
| 19 LogicTrace | Claude Sonnet / strongest code model | No fine-tuning in repo | N/A | Claude or top-tier code reasoning | Debug triage and execution tracing require deeper code analysis |
| 20 DocGen | Claude Sonnet / strongest technical writer | No fine-tuning in repo | N/A | Claude or top-tier writing model | Long-form documentation quality is better with stronger base technical writing |

## Core 3-Stage Fine-Tuning Tools

### QuizVerse (03)

**Best method**
- Stage 1: SFT + rsLoRA
- Stage 2: GRPO
- Stage 3: SimPO

**Why**
- must emit valid JSON reliably
- must produce correct answers and explanations
- must balance Bloom levels and difficulty
- quality can be measured with explicit rewards

**Training target**
- structured quiz generation
- explanation quality
- difficulty diversity
- pedagogical coverage

**Recommended datasets**
- SciQ
- ARC
- OpenBookQA
- MMLU subset
- self-curated educational JSON outputs

**Evaluation focus**
- JSON compliance
- answer correctness
- explanation quality
- Bloom coverage

**Current repo status**
- pipeline exists
- no trained Stage 1/2/3 checkpoint yet
- page currently runs base/local Gemma

### DSA Sage (10)

**Best method**
- Stage 1: SFT + rsLoRA on chain-of-thought-style tutoring outputs
- Stage 2: GRPO using step correctness + explanation clarity rewards
- Stage 3: SimPO on chosen vs rejected tutor responses

**Why**
- step-by-step reasoning matters more than surface fluency
- dry-run quality and explanation quality can be optimized directly
- interview-style pedagogy benefits from preference tuning

**Training target**
- problem decomposition
- stepwise reasoning
- correct complexity analysis
- high-quality teaching explanations

**Recommended datasets**
- self-curated DSA problems and worked solutions
- LeetCode-style public problems where licensing permits internal training prep
- self-play preference pairs from Stage 2 model

**Evaluation focus**
- solution correctness
- dry-run quality
- explanation usefulness
- complexity accuracy

**Current repo status**
- page exists and works on base Gemma
- no DSA-specific adapter yet

### Studio (13)

**Best method**
- Stage 1: SFT on flashcards, guides, summaries, timelines
- Stage 2: GRPO on artifact quality rewards
- Stage 3: SimPO on preference pairs scored for usefulness and clarity

**Why**
- Studio is the broadest artifact generator
- consistency across formats matters
- quality is visible to judges and end users immediately

**Training target**
- active-recall flashcards
- concise but complete summaries
- useful study guides
- strong educational structure

**Evaluation focus**
- flashcard quality
- summary density vs clarity
- usefulness of generated study guides

**Current repo status**
- page exists and is demoable
- no specialized Studio adapter yet

## Vision Fine-Tuning Tools

### NeuroRead (02)

**Best method**
- Vision LoRA / multimodal adapter
- optional grounded follow-up QA SFT after the vision adapter

**Why**
- photographed notes, textbook pages, and scanned content need better visual extraction
- document-grounded follow-ups benefit from context-specific refusal behavior

**Recommended vision datasets**
- DocVQA
- ChartQA subset
- InfographicVQA subset
- self-created textbook/note photos

**Recommended text follow-up dataset**
- `fine_tuning/prepare_context_qa_dataset.py`

**Current repo status**
- `vision_engine.py` exists now
- local `rag_engine.py` fallback exists now
- no actual vision fine-tuned model yet

### PaperAnalyzer (11)

**Best method**
- same vision adapter family as NeuroRead
- optional grounded QA SFT for academic follow-ups

**Why**
- academic PDFs include charts, layouts, and scanned figures
- paper QA quality depends on both extraction and grounding

**Current repo status**
- PDF + LightRAG flow exists
- no actual DocRead-style multimodal fine-tune yet

## Optional Stage-1-Only Tool

### PrepMaster (06)

**Best method**
- Optional instruction LoRA / Stage 1 only

**Why**
- structure matters, but reward optimization is less necessary than for QuizVerse
- high-quality prompting may already be enough for demo quality

**Current recommendation**
- only fine-tune if time remains after QuizVerse, DSA Sage, Studio, and vision adapter work

## Prompting-Only Gemma Tools

These tools are best served by a stronger base model plus task-specific prompts rather than custom tuning:

- NetSeek (01)
- EduTube (04)
- MindMapper (05)
- GraphiQ (07)
- WriteWise (08)
- CodeBuddy (09)
- AudioOverview (12)
- MultiSourceSynth (14)
- IdeaSpark (15)
- FeatureForge (16)

**Reason**
- open-ended generation quality matters more than rigid format compliance
- custom tuning risks narrowing creativity or generality
- retrieval, context handling, or prompt design drives quality more than domain adaptation

## Claude / Strongest Base Model Tools

Your original plan is directionally correct for these pages:

- CodeFlow (17)
- ArchViz (18)
- LogicTrace (19)
- DocGen (20)

If the judging environment allows API dependence, these are still the best candidates for Claude-class inference. If you must stay fully local, keep Gemma as the fallback but expect lower ceiling on code-analysis quality.

## Latest Best-Practice Methods Per Goal

### Best for structured educational outputs
- SFT + rsLoRA
- then GRPO
- then SimPO

### Best for grounded follow-up QA
- grounded SFT on context-only examples
- short conversation history during inference
- strict refusal examples when support is missing

### Best for document images and photographed notes
- multimodal vision LoRA on document/image QA
- optionally followed by grounded QA SFT

### Best for open-ended creative/product tasks
- stronger base model + prompt engineering
- avoid unnecessary fine-tuning

### Best for code analysis and technical docs
- strongest available code-native model
- do not spend Kaggle budget on domain adapters unless code reasoning is the main competition focus

## Current Gap Summary

### Already in repo
- 3-stage text fine-tuning scripts
- context-followup dataset generator
- local Gemma runtime
- LightRAG integration
- `rag_engine.py`
- `vision_engine.py`
- `function_calling.py`

### Still missing execution-wise
- actual Stage 1 SFT run
- actual GRPO run
- actual SimPO run
- actual vision fine-tuning run
- actual GGUF export of the final trained adapter/model

## Priority Order If Time Is Limited

1. QuizVerse adapter
2. Studio adapter
3. NeuroRead / PaperAnalyzer vision adapter
4. DSA Sage adapter
5. PrepMaster Stage-1-only adapter

Everything else should stay prompt-first unless you finish those five successfully.
