# Page-by-Page Demo Inputs

## NetSeek

Use query:

`Recent advances in retrieval-augmented generation for education`

Expected story:
- visible search sources
- source-aware synthesis
- grounded research brief

## EduTube

If transcript fetching works:
- paste a tested YouTube URL

If not:
- paste `audio_overview_transcript.txt`

Expected story:
- transcript to notes
- transcript to flashcards

## NeuroRead

Use source:
- `neuroread_sample_doc_1.txt`
- `neuroread_sample_doc_2.txt`

Ask:
1. `What is the difference between RAG and CAG in education?`
2. `Why does session memory matter for learners?`
3. `Which pattern is better for turning one chapter into flashcards?`

Expected story:
- grounded answer
- follow-up answer uses prior context
- visible source references

## QuizVerse

Use source:
- `rag_vs_cag_study_packet.txt`

Settings:
- 5 questions
- mixed difficulty
- mcq

Expected story:
- source becomes an assessment
- explanations support learning, not just scoring

## PrepMaster

Use source:
- `rag_vs_cag_study_packet.txt`

Goal:
- `Master the differences between RAG and CAG for an AI systems interview`

Settings:
- 2 weeks
- 6 hours per week

Expected story:
- source becomes a realistic study plan

## Studio

Use source:
- `rag_vs_cag_study_packet.txt`

Generate:
- flashcards
- study guide
- summary

Expected story:
- one source becomes multiple reusable artifacts

## AudioOverview

Use source:
- `audio_overview_transcript.txt`

Generate:
- `Podcast Script`
- then `Generate Audio Narration`

Expected story:
- transcript becomes an audio-friendly explainer

## MultiSourceSynth

Use sources:
- `rag_vs_cag_study_packet.txt`
- `audio_overview_transcript.txt`

Analysis type:
- `Compare & contrast`

Focus question:
- `How do these sources suggest learners should move from passive review to active learning?`

Expected story:
- cross-source reasoning with explicit source labels

## ArchViz

Use source:
- `microservices_architecture_brief.txt`

Diagram type:
- `System Architecture (C4 style)`

Expected story:
- product also supports technical/system design workflows

## LogicTrace

Use source:
- `logictrace_bug_report.txt`

Run:
- `Build Triage Plan`

Expected story:
- product also helps technical learners and builders debug complex systems
