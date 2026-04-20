# Hackathon Submission Notes

## One-line Pitch

SmartStudy AI is a Gemma-powered learning platform that turns raw study inputs into grounded answers, adaptive quizzes, study plans, flashcards, diagrams, and code-analysis artifacts.

## Problem

Students and self-learners have too many disconnected tools for too many disconnected content types.

They read PDFs in one place, watch videos in another, search the web separately, create notes manually, and still have to convert knowledge into practice on their own.

## Solution

SmartStudy AI brings that workflow together in one Gemma-first product.

- upload documents and ask grounded questions
- convert videos and transcripts into notes and flashcards
- generate quizzes and study plans
- synthesize multiple sources
- export everything into an Obsidian workflow
- support technical learners with code diagrams and debugging analysis

## Why Gemma

- local-first inference keeps the core product affordable and practical
- Gemma is used across the main generation paths, not as a token add-on
- the repository includes a fine-tuning path that shows how the project can evolve beyond prompting alone

## Technical Highlights

- **Gemma via Ollama** for local generation
- **LightRAG** for grounded document retrieval
- **Session-scoped workspaces** to reduce cross-session retrieval contamination
- **Source-aware web research** in NetSeek
- **YouTube transcript ingestion** in EduTube
- **Audio narration export** in AudioOverview
- **Mermaid-based visual outputs** for maps and code/architecture flows
- **Obsidian export** for practical downstream use

## Recommended Live Demo

1. `NetSeek`
   Show live web research with visible source links.
2. `EduTube`
   Paste a YouTube URL and generate notes or flashcards.
3. `NeuroRead`
   Upload documents and ask a grounded question with references.
4. `QuizVerse`
   Generate a quiz from the same study material.
5. `AudioOverview`
   Generate an audio-ready explanation and MP3 narration.
6. `MultiSourceSynth`
   Show synthesis across multiple sources.
7. `LogicTrace` or `CodeFlow`
   Show how the same platform supports technical learners and developers.

## Strongest Judging Angles

- breadth of product surface without losing coherence
- local Gemma integration across real workflows
- grounded RAG answers instead of purely freeform chat
- practical outputs learners can actually keep and reuse
- clear path to deeper model specialization through fine-tuning

## Current Constraints

- LightRAG must be running separately
- some secondary pages are still prompt-heavy rather than deeply tooled
- fine-tuning scripts exist, but training datasets still need to be prepared externally

## What To Emphasize In Submission

- this is not a single-use-case demo
- the system supports multiple input modalities and multiple output modalities
- the app shows a real product strategy around Gemma, not just a wrapper around a single prompt
