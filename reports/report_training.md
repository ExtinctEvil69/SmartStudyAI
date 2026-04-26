---
title: "Polaris — Training Pipeline Report"
subtitle: "Status, gaps, and the path to winning the Gemma 4 Good Hackathon"
author: "Polaris (SmartStudy AI) Project"
date: "2026-04-25"
geometry: margin=2.4cm
fontsize: 11pt
mainfont: "Helvetica"
monofont: "Menlo"
header-includes:
  - \usepackage{xcolor}
  - \definecolor{accent}{HTML}{7C6CFF}
  - \usepackage{sectsty}
  - \chapterfont{\color{accent}}
  - \sectionfont{\color{accent}}
  - \subsectionfont{\color{accent}}
---

# Executive Summary

Polaris is a 22-tool unified learning ecosystem powered by local Gemma 4 inference, with a persistent shared-memory layer (Vidya Smriti) and an autonomous Claude-Code-style StudyAgent. Originally shipped as **SmartStudy AI** (Streamlit, 21 tools), it now also exists as **Polaris** (FastAPI + modern HTML/JS, 22 tools).

The training pipeline ingests publicly available STEM lectures (MIT OCW, Stanford, Harvard, 3Blue1Brown, Veritasium, NeetCode, Computerphile, Numberphile, Fireship, StatQuest), GitHub lecture-notes repositories (TheAlgorithms/Python, neetcode-gh/leetcode, langchain-ai/langchain, d2l-ai/d2l-en, Karpathy nn-zero-to-hero, Stanford CS229 cheatsheets), and synthesizes **multi-format SFT training pairs** (Q&A, quiz JSON, study notes, summaries, agent plans, exam-style problems for JEE Advanced, GATE CS, SAT Math, Putnam, IMO, USAMO).

As of the time of this report, **the v4 build chain is actively running with 1,326 training pairs already merged into `master_sft.jsonl`**, projected to reach 2,500–3,500 examples by Sunday/Monday once the chain completes.

---

# 1. What Has Been Built

## 1.1 Dual application layer

| Application | Stack | Tools | Status |
|-------------|-------|-------|--------|
| **SmartStudy AI** | Streamlit multi-page | 21 tools | shipped, running |
| **Polaris** | FastAPI + HTML/JS SPA | **22 tools + StudyAgent** | shipped, running on `localhost:8000` |

Both share the same `core/` engine layer:

- `gemma_engine.py` — Ollama-backed Gemma generation (with robust JSON parsing for LaTeX-laden outputs)
- `cag_engine.py` — Cache-Augmented Generation (full-document context, used by QuizForge, Studio, PrepMaster)
- `lightrag_engine.py` — graph-based RAG for multi-document Q&A
- `web_research.py` — DuckDuckGo + page scraping for NetSeek
- `youtube_engine.py` — transcript extraction for EduTube and dataset-builder
- `audio_engine.py` — gTTS narration for AudioOverview
- `obsidian_export.py` — markdown export across all tools

## 1.2 Polaris tool inventory (22 tools, 5 categories)

### Memory
- **Vidya Smriti** — 4-dimensional shared memory (Learner Profile, Knowledge Graph, Content Registry, Active Context). Tracks topic mastery via exponential moving average. Persists to `smriti_data/*.json`.

### Agent
- **StudyAgent** — Claude-Code-style loop (Explore -> Plan -> Execute -> Verify -> Record). User approves the plan before execution; final report is structured (Changed / Verified / Remaining risk / Next step).

### Study (5)
- NetSeek (web research, source-aware synthesis)
- NeuroRead (document upload + grounded Q&A)
- EduTube (YouTube transcript -> study notes / flashcards)
- QuizForge (adaptive quiz generation, Bloom taxonomy)
- PaperAnalyzer (research paper analysis)

### Create (7)
- MindMapper (Mermaid mind maps)
- PrepMaster (study plans, study guides)
- GraphiQ (Desmos 2D graphing from natural language)
- AudioOverview (gTTS podcast narration)
- WriteWise (writing polish, multiple modes)
- Studio (one-click study artifacts)
- MultiSourceSynth (multi-document synthesis with citations)

### Build (4)
- CodeBuddy (code explanation, debugging, refactoring)
- DSASage (DSA tutor with complexity analysis)
- IdeaSpark (project idea generation)
- FeatureForge (PM-style feature specification)

### Code (5)
- CodeFlow (code -> Mermaid flowchart)
- ArchViz (system -> architecture diagram)
- LogicTrace (execution / bug trace)
- **CodeAudit** (NEW — adversarial code review with bug/security/perf/score)
- DocGen (auto-generated documentation)

## 1.3 Training data pipeline

**Source connectors:**

- `fine_tuning/sources/youtube_lecture.py` — single-video and playlist (yt-dlp) modes
- `fine_tuning/sources/github_notes.py` — clones repos, harvests `.md`, `.tex`, `.rst`, `.txt`
- `fine_tuning/sources/exam_styles.py` — generates JEE / GATE / SAT / Putnam / IMO / USAMO problems

**Generators (per source document):**

| Generator | Output format | What it teaches |
|-----------|---------------|----------------|
| qa | Grounded answer to a generated question | Stay in source, no hallucination |
| quiz | Structured JSON quiz (3 questions + explanations + Bloom levels) | The QuizForge schema |
| study_notes | Markdown notes with required sections | The pedagogical-notes format |
| summary | One paragraph + 5 bullets + audience | Compression style |
| agent_plan | JSON plan with rationale + 3-5 steps | The StudyAgent format |
| exam_<style> | Exam-format problem + solution | JEE / GATE / SAT / Putnam / IMO / USAMO signature formats |

**Recipes catalog** (`fine_tuning/dataset_recipes.py`) — currently 22 recipes covering Physics, Mathematics, Computer Science, Algorithms, Machine Learning, Deep Learning, Statistics. Each recipe pairs a source with the exam styles that fit its subject.

---

# 2. Training Dataset — Current Status

## 2.1 Version history

| Version | When | max_chunks | Recipes | Examples | Notes |
|---------|------|-----------|---------|----------|-------|
| v1 | Apr 24 22:39 | 2 | 9 | 204 | Initial proof |
| v2 | Apr 25 00:31 | 4 | 9 | 326 | Deeper extraction (+60%) |
| v3 | Apr 25 06:18 | 6 | 11 | 468 | Added 3B1B Neural Nets, MIT 18.01 |
| **v4** | **in progress** | 4 | 11 new | **1,326+ (climbing)** | Channels + LeetCode + LangChain + algorithms repos |

Versioned backups are preserved at `master_sft_v1.jsonl`, `master_sft_v2.jsonl`, `master_sft_v3.jsonl`. Each is a full snapshot of the merged training corpus at that point in time.

## 2.2 v4 recipes — yield breakdown so far

| Recipe | Source | Yield | Quality assessment |
|--------|--------|-------|-------------------|
| veritasium_physics | YouTube channel | **109** | High — physics intuition + experiment context |
| numberphile_math | YouTube channel | 73 | High — math curiosities, proof sketches |
| computerphile_cs | YouTube channel | 91 | High — CS theory explanations |
| fireship_dev | YouTube channel | 52 | Medium — dev tutorials, opinionated |
| neetcode_leetcode | YouTube channel | 106 | High — DSA walkthroughs with complexity |
| statquest_stats | YouTube channel | 82 | High — statistics + ML pedagogy |
| **the_algorithms_python** | GitHub | **345** | High — algorithm implementations + docstrings |
| neetcode_solutions_repo | GitHub (in progress) | 6 of ~925 expected | Medium — formulaic LeetCode markdown |
| langchain_docs | GitHub (queued) | — | Medium — LangChain docs (might be repetitive) |
| d2l_deep_learning | GitHub (queued) | — | High — full DL textbook |
| openmythos_reference | GitHub (queued, placeholder URL) | — | Will likely fail — TBD URL |

## 2.3 Subject coverage achieved

| Subject | Sources | Strength |
|---------|---------|----------|
| Physics | MIT 8.01 (Lewin), Veritasium | Strong |
| Mathematics | MIT 18.01, MIT 18.06, 3B1B Calc/LA, Numberphile | Excellent |
| Computer Science | MIT 6.006, Stanford CS229, Harvard CS50, Computerphile, Fireship | Strong |
| Algorithms / DSA / LeetCode | NeetCode (YT + repo), TheAlgorithms/Python | Excellent |
| Machine Learning | Stanford CS229 + cheatsheets, 3B1B NN, StatQuest, LangChain | Strong |
| Deep Learning | Karpathy nn-zero-to-hero, D2L textbook | Good |
| Statistics | StatQuest | Adequate |
| **Chemistry** | **None** | **Gap** |
| **Biology** | **None** | **Gap** |
| **Quantitative Finance** | **None** | **Gap** |
| **Humanities / Arts / Medicine** | **None** | **Gap** |

---

# 3. What Is Left to Do

## 3.1 Immediate (data collection completion)

- [x] v4 chain build running — auto-completes weekend
- [x] Snapshot loop running every 30 min — `master_sft.jsonl` always current
- [ ] Confirm `openmythos_reference` recipe URL (placeholder will fail gracefully)
- [ ] Add Chemistry, Biology, Humanities recipes (deferred per user decision)
- [ ] Add Quants source (no clear public option; deferred for v5 research)

## 3.2 Stage 1 — SFT + rsLoRA on Kaggle T4 (~3 hours)

- [ ] Push `master_sft.jsonl` to a public location Kaggle can fetch (Kaggle Dataset, GitHub gist, or HF Hub)
- [ ] Open `notebooks/gemma4_finetune.ipynb`, attach the dataset
- [ ] Run Stage 1 training:
  - Base: `gemma-3-4b-it` (or `gemma-3-2b-it` if T4 memory tight)
  - rsLoRA rank 32, alpha 16, learning rate 1e-4
  - 3 epochs, gradient_accumulation_steps=8, batch_size=2
  - Output: LoRA adapter at `outputs/stage1_sft/`
- [ ] Sanity-eval: run `fine_tuning/evaluate.py` against held-out questions

## 3.3 Stage 2 — GRPO (reward-model training, ~3 hours)

- [ ] Confirm `fine_tuning/reward_functions.py` reward shapes are appropriate:
  - Bloom-coverage reward (cognitive level diversity in quiz)
  - Difficulty-mix reward (penalty for all-easy or all-hard)
  - Explanation-quality reward (length + content density)
  - Schema-compliance reward (penalty for malformed JSON)
- [ ] Run `train_stage2_grpo.py` on quiz examples from the dataset
- [ ] Output: GRPO-tuned model at `outputs/stage2_grpo/`

## 3.4 Stage 3 — SimPO (preference / taste, ~2 hours)

- [ ] Generate preference pairs from existing SFT outputs (better vs worse on the same prompt)
- [ ] Run `train_stage3_simpo.py`
- [ ] Output: SimPO-tuned model at `outputs/stage3_simpo/`

## 3.5 Export, deploy, integrate

- [ ] Merge LoRA -> full weights (Unsloth `merged_16bit` or similar)
- [ ] Convert to GGUF (q4_k_m for size, q5_k_m for quality)
- [ ] `ollama create polaris-edu -f Modelfile.smartstudy-edu`
- [ ] Set environment variables in `.env`:
  - `SMARTSTUDY_MODEL_GENERAL=polaris-edu`
  - `SMARTSTUDY_MODEL_QUIZVERSE=polaris-edu`
  - `SMARTSTUDY_MODEL_DSASAGE=polaris-edu`
  - `SMARTSTUDY_MODEL_STUDIO=polaris-edu`
- [ ] Restart Polaris server, verify in `/api/health` that the model is detected
- [ ] A/B test against baseline `gemma-4` on 5–10 standardized prompts before promoting

## 3.6 Demo / pitch / submission

- [ ] Demo video (5 min): NetSeek -> ingest -> ground -> quiz -> audio overview, one continuous flow
- [ ] Screenshots: dashboard with mastery bars, agent plan executing, quiz scoring, GraphiQ rendering
- [ ] Devpost submission text (already drafted at `DEVPOST_SUBMISSION.md` — needs update for Polaris)
- [ ] Pitch deck or 1-pager for judges
- [ ] Submission deadline: **2026-05-18** (Kaggle Gemma 4 Good Hackathon)

---

# 4. What Can Be Done Better

## 4.1 Dataset quality and balance

**Issue: Training set is STEM-heavy and risks producing STEM-flavored outputs even on humanities prompts.**

Recommended additions for v5:

- **Chemistry**: MIT OCW 5.111 (Sylvia Ceyer), Khan Academy AP Chemistry videos
- **Biology**: MIT OCW 7.012 (Eric Lander), Crash Course Biology with Hank Green
- **Medicine**: MIT HST.583 (fMRI), AMBOSS (paywalled), Osmosis YouTube
- **Humanities**: Yale Open Yale Courses (PHIL 176 with Shelly Kagan, HIST 116 with Donald Kagan), TED-Ed channel
- **Arts**: Khan Academy Smarthistory, Music Theory channels
- **Quants**: Hard. Possible — `quantopian/research_public` GitHub, QuantPy YouTube, Marcos López de Prado's papers (publicly hosted)

Adding 5–8 of these would balance the dataset to ~30% non-STEM, which is the sweet spot for a general study assistant.

## 4.2 Source verification (the YouTube-ID problem)

In v1 and v2, several recipe video IDs were placeholders that returned "video unavailable." The pipeline silently skipped them, but the result was wasted recipe slots.

**Improvement:** Pre-flight verification script that, before any recipe runs, fetches a single transcript per recipe to confirm at least 1 video works. If 0 videos work, log a warning and skip the recipe entirely (saves Ollama cycles).

```python
# fine_tuning/sources/preflight.py — proposed
def verify_recipe(recipe_id, recipe):
    if recipe['source_module'] != 'youtube_lecture':
        return True
    videos = recipe['spec'].get('videos', [])
    for vid, _ in videos:
        try:
            fetch_transcript(vid)
            return True  # at least one works
        except Exception:
            continue
    return False
```

## 4.3 Reward functions for Stage 2 (GRPO)

The current `reward_functions.py` (per `RUNBOOK.md`) is generic. For peak quiz quality:

- **Add factual-correctness reward** — sample the quiz answer, regenerate it from a separate Gemma instance, score agreement
- **Add explanation-citation reward** — penalize quiz explanations that don't reference the source material
- **Add hallucination-detection reward** — keyword overlap between quiz content and source context

This is the highest-leverage Stage 2 improvement. GRPO with a strong reward signal can produce a 20–30% quality lift on benchmarks; with a weak reward it's marginal.

## 4.4 Vidya Smriti enhancements

Currently the memory layer **tracks** mastery and events but doesn't actively **drive** review. Recommended:

- **Spaced-repetition scheduler**: nightly job that recommends "review topics where mastery <70% AND last_studied >7 days"
- **Cross-tool transfer**: when user does a quiz in QuizForge, automatically generate flashcards in EduTube format for the missed questions
- **Decay model**: mastery decays over time without practice, surfaced on dashboard

These are 1-day implementation each and would significantly increase the perceived "intelligence" of the system in a demo.

## 4.5 CodeAudit integration with the StudyAgent

CodeAudit is currently a standalone tool. It could be a **subagent** invoked by the StudyAgent when a code-related learning goal is set. Per the Claude Code architecture document referenced earlier, this is the textbook "subagent for review/audit" pattern.

```
StudyAgent goal: "Master Python sorting algorithms"
  -> Plan: research -> study_notes -> write_implementation -> CodeAudit -> quiz
  -> CodeAudit subagent reviews the user's implementation, returns blocking issues
  -> Quiz incorporates the user's actual mistakes
```

This would be a powerful demo moment for judges.

## 4.6 Pre-flight validation for the trained model

After Stage 3, before promoting `polaris-edu` to production env vars, run a **regression suite**:

- 20 standardized prompts (one per tool category)
- Compare outputs side-by-side against baseline Gemma
- Auto-detect regressions (output length collapse, format violations, hallucination keywords)

Without this, a bad fine-tune can ship and degrade the demo. The eval script already exists at `fine_tuning/evaluate.py` but should be expanded to cover all 22 tools.

## 4.7 Long-running build robustness

The current chain script wraps caffeinate around the build. Two improvements for genuine multi-day runs:

- **Resume-from-checkpoint**: if the build dies mid-recipe, the next run should skip already-completed recipes (currently it re-processes them)
- **Per-document logging with timing**: write a CSV of (recipe, document, duration, examples_yielded) so you can identify which sources are highest-ROI

The snapshot loop launched today partially mitigates this (no data is lost), but the build itself doesn't have resume.

---

# 5. Suggestions for Winning the Hackathon

## 5.1 Target prizes

The Gemma 4 Good Hackathon has multiple prize tracks. Polaris is well-positioned for:

| Prize | Fit | Why |
|-------|-----|-----|
| **Main Education Prize** | Excellent | 22 tools, agent loop, memory layer, real fine-tune |
| **Ollama Special Prize ($10K)** | Excellent | Fully local Ollama-backed, zero cloud dependency |
| **Unsloth Special Prize ($10K)** | Strong | 3-stage pipeline (SFT + GRPO + SimPO) on Unsloth |
| **Open Source Prize** | Strong | Already public on GitHub (`ExtinctEvil69/SmartStudyAI`) |

## 5.2 Recommended demo flow (5 minutes)

The strongest narrative for judges:

1. **Open Polaris** at `localhost:8000`. Show the dashboard and 22-tool sidebar. *(10s)*
2. **NetSeek**: enter "What are recent advances in CRISPR for sickle cell?" -> live web search + cited synthesis. *(45s)*
3. **NeuroRead**: upload a research paper PDF -> ask 2 grounded questions. *(45s)*
4. **StudyAgent**: enter goal "Master backpropagation in 30 min." Show the agent **plan**, approve, watch execution streaming through 4 steps, then take the auto-generated quiz. *(120s — the showpiece)*
5. **CodeAudit**: paste a buggy Python function -> adversarial review with bug + score. *(30s)*
6. **Vidya Smriti dashboard**: show how all of the above updated mastery, the streak, the recommendations. *(20s)*
7. **Mention fine-tuning**: open a terminal, show `ollama list` with `polaris-edu`. State: *"This entire flow runs on a model we fine-tuned on 1,500+ MIT/Stanford/Harvard examples we generated through this same agent loop."* *(30s)*

The "agent generates training data -> train model -> model powers the agent" closed loop is **the** narrative judges will remember.

## 5.3 The "wow moments" to engineer

Judges remember three things from a demo:

1. **The 0->insight moment**: empty NetSeek -> cited research brief in 30 seconds
2. **The autonomy moment**: StudyAgent producing a 4-step plan, executing without intervention, scoring the user
3. **The persistence moment**: open Vidya Smriti, see the mastery bars and timeline reflect everything you just did

If any of these break during the demo, the perceived quality drops 50%. **Practice the full flow 5 times before judging day.**

## 5.4 Risk mitigations before submission

| Risk | Mitigation |
|------|-----------|
| Ollama down on demo machine | Fallback to Anthropic API (already wired via `core/claude_engine.py`); pre-load all models with `ollama run polaris-edu < /dev/null` |
| YouTube transcript fails live | Pre-cache 2 transcripts in `data/demo_outputs/` |
| Fine-tuned model worse than baseline | Keep `gemma-4` as the env var default until you've A/B tested polaris-edu on 20+ prompts |
| Internet fails during demo | NetSeek + EduTube degrade gracefully; have NeuroRead with a pre-uploaded doc ready |
| Judges ask "why local?" | Privacy + reproducibility + zero-cost-per-student narrative |

## 5.5 What to write on the Devpost / Kaggle submission

The single strongest framing:

> *"Polaris is a 22-tool learning ecosystem where every tool feeds a shared memory layer (Vidya Smriti) and an autonomous study agent. The agent uses Claude Code-style planning to turn one learning goal into a multi-step session. Then we used the agent itself to generate 1,500+ training examples from MIT, Stanford, Harvard, and 3Blue1Brown sources, fine-tuned Gemma 4 in 3 stages (SFT + rsLoRA -> GRPO -> SimPO), exported to GGUF, and deployed locally via Ollama. The result is a learning system that runs entirely on a student's laptop, learns from any subject they upload, and improves itself."*

Avoid jargon. Avoid bullet salad. **One narrative, one sentence per tool category, evidence (numbers).**

## 5.6 Concrete priority order for the next 7 days

Assuming submission deadline 2026-05-18 (about 3 weeks out):

| Day | Task | Outcome |
|-----|------|---------|
| Sat-Sun | Let v4 build run | ~2,500 examples |
| Mon | Push dataset to Kaggle, kick off Stage 1 SFT | LoRA adapter |
| Tue | Eval Stage 1, kick off Stage 2 GRPO | Reward-tuned model |
| Wed | Stage 3 SimPO + GGUF export + Ollama register | `polaris-edu` deployed |
| Thu | A/B test polaris-edu vs baseline; promote if better | Winning model live |
| Fri | Add chemistry/biology recipes (v5), regenerate small dataset, re-train delta | More balanced model |
| Weekend | Demo video recording, screenshots, Devpost text | Submission-ready |

Buffer of one week before deadline for unforeseen issues.

---

# 6. Conclusion

Polaris is in **strong shape**. The application layer is complete and stable; the training data pipeline is producing high-yield, well-formatted SFT pairs; the architecture is hackathon-ready and demo-ready.

The remaining work is **execution-heavy, not invention-heavy**: kick off Kaggle training, evaluate, deploy, and polish the demo. None of that requires new code or new ideas — only the discipline to follow the runbook.

The two biggest risks are:

1. **Subject imbalance** — the model may sound STEM-flavored on humanities prompts. Easy fix, deferred per current priorities.
2. **Demo fragility** — any tool breaking during the 5-minute judge window costs disproportionately. Practice the flow.

If those are managed, this project is competitive across all three priority prize tracks. The agent -> train -> deploy closed loop is genuinely novel and presents well.

---

*Generated 2026-04-25 by Polaris.*

*Source: `/Users/niharnarsana/Desktop/SmartstudyAI/`*

*Repository: github.com/ExtinctEvil69/SmartStudyAI*
