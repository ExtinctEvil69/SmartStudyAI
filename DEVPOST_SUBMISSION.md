# Devpost Submission Draft

## Project Name

SmartStudy AI

## Tagline

A Gemma-powered learning platform that turns raw study inputs into grounded answers, quizzes, study plans, flashcards, audio explainers, and technical artifacts.

## What It Does

SmartStudy AI helps students, self-learners, and knowledge workers turn fragmented learning material into structured, reusable study outputs.

The platform supports multiple input types, including:

- PDFs and research papers
- web research topics
- YouTube videos and transcripts
- lecture notes and pasted text
- podcasts and audio transcripts
- technical code and system descriptions

From those inputs, SmartStudy AI can generate:

- grounded document Q&A
- web research briefs with sources
- quizzes with explanations
- study plans
- flashcards and summaries
- multi-source synthesis
- audio-style explainers and MP3 narration
- code flowcharts, architecture diagrams, and debugging plans

## Inspiration

Learning is fragmented. Students constantly move between PDFs, notes, videos, papers, search engines, flashcard apps, and separate AI tools, but those workflows rarely connect into a coherent learning loop.

We wanted to build a single Gemma-powered platform that could take raw learning inputs and turn them into grounded, practical outputs that learners can actually use.

## How We Built It

SmartStudy AI is built as a multipage Streamlit application.

Core architecture:

- **Gemma via Ollama** powers the main generation workflows locally
- **LightRAG** powers grounded document retrieval and graph-backed question answering
- **CAG workflows** are used when the full source is already available in context
- **Obsidian export** makes the outputs reusable outside the app

We also included an open-source fine-tuning path in the repository:

- Stage 1: SFT + rsLoRA
- Stage 2: GRPO
- Stage 3: SimPO
- Evaluation and GGUF export

To strengthen context-following behavior, we also added a grounded follow-up QA dataset generator for future open-source Gemma fine-tuning.

## Challenges We Ran Into

- keeping answers grounded instead of overly generic
- coordinating multiple workflows inside one coherent app
- making document retrieval work reliably in demo conditions
- balancing local-first inference with breadth of features
- handling follow-up questions without losing context

## Accomplishments That We’re Proud Of

- built a full multipage learning product instead of a single prompt demo
- integrated local Gemma across real user workflows
- added LightRAG-backed grounded Q&A with references
- supported multiple output types: quizzes, plans, guides, audio, diagrams, and exports
- created a hackathon-ready demo path with judge materials and repeatable sample inputs
- included an honest open-source training path instead of stopping at prompt engineering

## What We Learned

- the best educational AI tools are not only about answer generation, but about transforming content into active learning
- grounding and source visibility matter a lot for trust
- local Gemma inference can support a surprisingly broad product surface when paired with good workflow design
- small improvements in context retention make follow-up interactions feel much more useful

## What’s Next For SmartStudy AI

- improve citation rendering with chunk previews and richer references
- package the full demo setup even more cleanly for one-command startup
- run the fine-tuning pipeline on GPU with the new grounded context-followup dataset
- add evaluation assets for specialized Gemma checkpoints
- add screenshots, demo video, and polished visual assets for submission

## Built With

- Python
- Streamlit
- Gemma
- Ollama
- LightRAG
- Plotly
- gTTS
- youtube-transcript-api
- duckduckgo-search
- pypdf
