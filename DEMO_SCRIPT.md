# Demo Script

## 30-Second Opening

SmartStudy AI is a Gemma-powered learning platform that turns raw study inputs into grounded answers, quizzes, study plans, flashcards, audio explainers, and technical diagrams. It combines local Gemma inference, LightRAG for grounded retrieval, and exportable learning artifacts in one product.

## 3-Minute Demo

### 1. NetSeek
Say:
"We start with live research. Instead of generic AI output, NetSeek searches the web and keeps the source trail visible."

Do:
- open `NetSeek`
- use a query from `assets/demo_inputs/netseek_queries.md`
- show the generated brief and visible sources

### 2. EduTube
Say:
"Next, the same platform turns video learning into study material."

Do:
- open `EduTube`
- paste a YouTube URL or use transcript fallback material
- generate notes or flashcards

### 3. NeuroRead
Say:
"Here is the grounded document workflow. We upload source material, index it into LightRAG, and ask follow-up questions with session memory."

Do:
- open `NeuroRead`
- upload `assets/demo_inputs/neuroread_sample_doc_1.txt` and `assets/demo_inputs/neuroread_sample_doc_2.txt`
- ask one question, then a follow-up question
- show the sources panel

### 4. QuizVerse
Say:
"Once the learner understands the material, the system can immediately convert it into active recall."

Do:
- open `QuizVerse`
- reuse the same study packet
- generate a 5-question quiz

### 5. AudioOverview
Say:
"And for different learning styles, the system can turn the material into an audio-ready explanation."

Do:
- open `AudioOverview`
- use `assets/demo_inputs/audio_overview_transcript.txt`
- generate a podcast-style output and show MP3 generation

### Closing
Say:
"So the value here is not one isolated AI feature. It is a full Gemma-powered learning workflow: search, ingest, ground, explain, quiz, summarize, and export."

## 5-Minute Demo

Use the 3-minute flow above, then add:

### 6. MultiSourceSynth
Say:
"The platform can also reason across multiple sources instead of a single document."

Do:
- use the study packet plus the audio transcript
- run synthesis
- show source-aware output

### 7. LogicTrace or CodeFlow
Say:
"We also support technical learners and developers, so the same product extends beyond traditional study notes."

Do:
- open `LogicTrace` with `assets/demo_inputs/logictrace_bug_report.txt`
or
- open `CodeFlow` with any concise code sample

## Backup Demo Path

If network-dependent tools are unstable, use:

1. `NeuroRead`
2. `QuizVerse`
3. `PrepMaster`
4. `Studio`
5. `AudioOverview`
6. `LogicTrace`

This path still tells a strong Gemma-first story without depending on web search or transcript fetching.

## Key Lines To Repeat

- "Gemma is not a bolt-on here. It powers the core generation path across the product."
- "We use RAG when grounding matters and CAG when the full context is already available."
- "The product converts passive content into active learning."
- "The repo also includes an open-source fine-tuning path for better grounded context-following behavior."
