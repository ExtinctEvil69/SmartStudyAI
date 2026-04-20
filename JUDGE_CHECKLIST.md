# Judge Checklist

## Before Demo

1. Start Ollama
   - `ollama serve`
2. Confirm Gemma model exists
   - `ollama list`
3. Launch SmartStudy AI
   - `./judge_demo.sh`
4. Open homepage and verify:
   - Gemma status is green
   - LightRAG status is green
5. Keep `assets/demo_inputs/` open in a file browser or editor
6. Keep `PITCH_60_SECONDS.md` open for the opening if needed

## Pre-Warm Steps

1. Run one short prompt in `NetSeek`
2. Open `EduTube` once
3. Open `NeuroRead` once
4. If using `AudioOverview`, generate a short narration once before judging

## What To Avoid Live

1. Don’t upload giant PDFs for the first demo step
2. Don’t rely on untested YouTube URLs
3. Don’t switch models mid-demo
4. Don’t start with the most complex page first

## Best First Impression Order

1. Homepage
2. NetSeek
3. EduTube
4. NeuroRead
5. QuizVerse
6. AudioOverview

## Backup Plan If Something Fails

If web search or transcript fetching is unstable:

1. Use `assets/demo_inputs/neuroread_sample_doc_1.txt`
2. Use `assets/demo_inputs/neuroread_sample_doc_2.txt`
2. Use `assets/demo_inputs/audio_overview_transcript.txt`
3. Demo `NeuroRead`, `QuizVerse`, `PrepMaster`, `Studio`, `AudioOverview`

## Final Message

End with:

"SmartStudy AI is a Gemma-powered product, not just a one-off prompt demo. It combines grounded retrieval, study artifact generation, context-aware follow-up answers, and practical export in one learning workflow."
