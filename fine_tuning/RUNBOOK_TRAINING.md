# SmartStudy AI — Training Runbook

End-to-end pipeline: **gather data → build SFT dataset → train Gemma on Kaggle → export GGUF → deploy to Ollama**.

---

## 1. The mental model

```
                                  ┌──────────────────────────┐
  YouTube playlists ─────────►    │  fine_tuning/sources/    │
  GitHub repos      ─────────►    │  - youtube_lecture       │
  OCW courses       ─────────►    │  - github_notes          │
                                  │  - exam_styles           │
                                  └────────────┬─────────────┘
                                               │
                          (chunks, runs Gemma) │
                                               ▼
                                  ┌──────────────────────────┐
                                  │  fine_tuning/            │
                                  │   datasets/              │
                                  │   ├── mit_801_sft.jsonl  │
                                  │   ├── stanford_cs229...  │
                                  │   ├── exam_putnam_*      │
                                  │   └── master_sft.jsonl   │ ◄── train on this
                                  └────────────┬─────────────┘
                                               │
                                  (Kaggle T4, ~3-6h)
                                               ▼
                                  ┌──────────────────────────┐
                                  │  Stage 1: SFT + rsLoRA   │
                                  │  Stage 2: GRPO (reward)  │
                                  │  Stage 3: SimPO (taste)  │
                                  └────────────┬─────────────┘
                                               │
                                  (export GGUF)
                                               ▼
                                  ┌──────────────────────────┐
                                  │  ollama create           │
                                  │  smartstudy-edu          │
                                  └──────────────────────────┘
```

---

## 2. What gets generated per source

For every source document (a lecture transcript / notes file), the master builder runs **6 generators** that produce 6 training pairs:

| Generator | Input | Output | Why it matters |
|-----------|-------|--------|----------------|
| `qa` | Source text + question | Grounded answer | Teaches the model to stay in source, not hallucinate |
| `quiz` | Source text | Quiz JSON with explanations | Teaches the **QuizForge schema** — required for Stage 2 GRPO |
| `notes` | Source text | Markdown study notes | Teaches the **study notes format** with Key Concepts / Examples / Review Questions |
| `summary` | Source text | Para + 5 bullets | Teaches compression style |
| `agent_plan` | Topic + goal | JSON plan with rationale | Teaches the **StudyAgent format** — this is the Claude Code-style agentic output |
| `exam_<style>` | Source text + topic | Exam-format problem + solution | Teaches signature formats: JEE / GATE / SAT / Putnam / IMO / USAMO |

So a single 30-min lecture → **typically 6–10 training pairs** depending on transcript length and recipe config.

---

## 3. The recipes catalog

[`fine_tuning/dataset_recipes.py`](dataset_recipes.py) is the single source of truth. Currently included:

| Recipe ID | Source | Subject | Exam styles |
|-----------|--------|---------|-------------|
| `mit_801_physics` | MIT 8.01 (Walter Lewin) | Physics | `jee_advanced`, `putnam` |
| `mit_1806_linear_algebra` | MIT 18.06 (Strang) | Mathematics | `putnam`, `imo`, `gate_cs` |
| `mit_6006_algorithms` | MIT 6.006 | CS | `gate_cs` |
| `stanford_cs229_ml` | Stanford CS229 (Ng) | ML | `gate_cs` |
| `harvard_cs50` | Harvard CS50 (Malan) | CS | `gate_cs` |
| `3b1b_calculus` | 3Blue1Brown | Math | `jee_advanced`, `putnam` |
| `3b1b_linear_algebra` | 3Blue1Brown | Math | `putnam`, `gate_cs` |
| `stanford_cs229_cheatsheets` | GitHub: afshinea/stanford-cs-229-machine-learning | ML | `gate_cs` |
| `karpathy_nn_zero_to_hero` | GitHub: karpathy/nn-zero-to-hero | DL | `gate_cs` |

> **Important — video IDs require verification.** YouTube transcript availability changes (videos go private, captions get removed). Run a small dry-run first (see §6) before queueing a long build. If a video fails, the pipeline skips it and continues.

---

## 4. Adding more sources (the part you actually want to do)

### 4a. Add a YouTube lecture series

**Option A: explicit video list** (always works — no extra installs):

```python
# fine_tuning/dataset_recipes.py
"my_new_course": {
    "source_module": "youtube_lecture",
    "subject": "Statistics",
    "exam_styles": ["gate_cs", "sat_math"],
    "max_chunks": 2,
    "spec": {
        "subject": "Statistics",
        "videos": [
            ("VIDEO_ID_1", "Course Name — Lecture 1: Intro"),
            ("VIDEO_ID_2", "Course Name — Lecture 2: Probability"),
            # ... as many as you want
        ],
    },
},
```

**Option B: extract from a playlist** (needs `yt-dlp`):

```bash
.venv/bin/pip install yt-dlp
```

Then:

```python
"my_new_course": {
    "source_module": "youtube_lecture",
    "subject": "Statistics",
    "exam_styles": ["gate_cs"],
    "max_chunks": 2,
    "spec": {
        "subject": "Statistics",
        "playlist_url": "https://www.youtube.com/playlist?list=PLxxxxxx",
        "max_videos": 25,
    },
},
```

### 4b. Add a GitHub lecture-notes repo

Look for repos that contain `.md`, `.tex`, `.rst`, or `.txt` files (the source connector skips binaries):

```python
"my_lecture_notes": {
    "source_module": "github_notes",
    "subject": "Operating Systems",
    "exam_styles": ["gate_cs"],
    "max_chunks": 1,
    "spec": {
        "repo": "owner/reponame",
        "subject": "OS",
        "subdir": "lectures",   # optional — only this subfolder
    },
},
```

Good repos to start with (real, public):
- `mit-pdos/6.S081-2020-labs`
- `afshinea/stanford-cs-229-machine-learning`
- `karpathy/nn-zero-to-hero`
- `yandexdataschool/Practical_RL`
- `florinpop17/app-ideas`  (project idea descriptions)

### 4c. Add a new exam style

Edit [`fine_tuning/sources/exam_styles.py`](sources/exam_styles.py) and add an entry to `EXAM_TEMPLATES`:

```python
"my_exam": {
    "subject_match": ["physics", "math"],
    "format": "MyExam (description)",
    "instruction": """Create a MyExam-style problem...

Output JSON: {...exact schema...}""",
},
```

Then reference it in any recipe's `exam_styles` list.

### 4d. Reading YouTube descriptions for source links (your specific ask)

The current YouTube source pulls the **transcript** only. If a video description points to a free PDF, you have two paths:

1. **Manual once-off:** copy the PDF URL, save to `inputs/`, then write a tiny new recipe that reads it via `core/file_engine.py` (or just paste the text into a new GitHub repo and use `github_notes`).
2. **Automated:** write a new source module `fine_tuning/sources/yt_description_links.py` that uses `yt-dlp --get-description` to extract URLs and downloads the linked PDFs/HTML. ~80 lines. Tell me when you want this and I'll add it.

---

## 5. Running the master builder

```bash
# Build everything in the catalog (takes hours, kicks off many Gemma calls)
.venv/bin/python3 fine_tuning/build_master_dataset.py

# Or: just specific recipes
.venv/bin/python3 fine_tuning/build_master_dataset.py \
    --recipes mit_801_physics 3b1b_calculus stanford_cs229_ml

# Smaller / faster for testing
.venv/bin/python3 fine_tuning/build_master_dataset.py \
    --recipes mit_801_physics --max-docs-per-recipe 1 --max-chunks 1

# With a different Ollama model (e.g. a more capable one for data gen)
.venv/bin/python3 fine_tuning/build_master_dataset.py --model gemma3:latest
```

**Throughput on M-series Mac with Gemma3:**
- ~13s per `qa`, 20s per `quiz`, 30s per `notes`, 14s per `summary`, 20s per exam pair.
- One lecture → ~2 minutes of compute.
- 10 lectures across 3 recipes → ~30–45 minutes.
- The full catalog (50+ documents) → 3–6 hours overnight.

The script writes per-recipe JSONLs **and** a merged `master_sft.jsonl`. Each run **overwrites** the per-recipe files but you can rerun selectively.

---

## 6. Inspecting / cleaning the dataset

```bash
# How many examples in each file?
wc -l fine_tuning/datasets/*.jsonl

# Look at one
.venv/bin/python3 -c "
import json
for line in open('fine_tuning/datasets/master_sft.jsonl'):
    ex = json.loads(line)
    print(ex['messages'][0]['content'][:120], '...')
    print('  ->', ex['messages'][1]['content'][:120], '...')
    print()
" | head -30

# Validate every line is valid JSON (catches truncation)
.venv/bin/python3 -c "
import json
ok, bad = 0, 0
for line in open('fine_tuning/datasets/master_sft.jsonl'):
    try: json.loads(line); ok += 1
    except: bad += 1
print(f'{ok} valid / {bad} invalid')
"
```

If you see truncated outputs (a quiz cut off mid-question), bump `max_tokens` in the relevant generator and rerun.

---

## 7. Training on Kaggle (the actual fine-tuning)

The dataset is now ready to train. Open [`notebooks/gemma4_finetune.ipynb`](../notebooks/gemma4_finetune.ipynb) and:

1. **Upload your dataset.** Either:
   - Push `fine_tuning/datasets/master_sft.jsonl` to a public GitHub repo and `wget` it in Kaggle, OR
   - Create a Kaggle Dataset and attach it to the notebook.

2. **Make sure the notebook reads it.** The training script `fine_tuning/train_stage1_sft.py` already expects the OpenAI-style `messages` format we produce.

3. **Stage 1 (SFT + rsLoRA)** — ~1.5–3h on T4:
   - Loads `gemma-3-4b-it` (or your chosen base)
   - Trains LoRA adapters on `master_sft.jsonl`
   - Saves to `outputs/stage1_sft/`

4. **Stage 2 (GRPO)** — ~2–4h, optional but big quality gain:
   - Uses `fine_tuning/reward_functions.py` to score quiz outputs on Bloom coverage, difficulty mix, explanation quality
   - The model learns to produce *better* quizzes than baseline
   - Output: `outputs/stage2_grpo/`

5. **Stage 3 (SimPO)** — ~1–2h, taste tuning:
   - Self-play preference learning
   - Output: `outputs/stage3_simpo/`

6. **Merge LoRA → full weights → GGUF:**

```bash
# In the notebook (or locally with enough RAM)
python fine_tuning/export_gguf.py \
    --base gemma3:latest \
    --adapter outputs/stage3_simpo \
    --output smartstudy-edu.gguf \
    --quant q4_k_m
```

---

## 8. Deploying to Ollama

```bash
# Use the provided Modelfile template
cp fine_tuning/Modelfile.smartstudy-edu.template Modelfile.smartstudy-edu
# Edit Modelfile.smartstudy-edu — point FROM at your local GGUF path

ollama create smartstudy-edu -f Modelfile.smartstudy-edu
ollama list   # confirm it appears

# Wire it into SmartStudy
echo "SMARTSTUDY_MODEL_GENERAL=smartstudy-edu" >> .env
echo "SMARTSTUDY_MODEL_QUIZVERSE=smartstudy-edu" >> .env
```

Restart your apps:
```bash
./brahmavidya/run.sh   # FastAPI
streamlit run main.py   # Streamlit
```

The sidebar status pill should now show your fine-tuned model selected.

---

## 9. "Keep training the model"

Fine-tuning is **not continuous** — each run produces a new model checkpoint. You "keep training" by:

1. **Periodically expanding the dataset.**
   - Add new recipes (every week or so).
   - Re-run `build_master_dataset.py` to regenerate.
   - The merged `master_sft.jsonl` grows.

2. **Re-running the Kaggle notebook** with the bigger dataset. Each run takes ~3–6h. Realistic cadence: once every 2–3 weeks during the hackathon, or after each major dataset addition.

3. **Versioning your models:**
   ```bash
   ollama create smartstudy-edu-v1 -f Modelfile.v1
   ollama create smartstudy-edu-v2 -f Modelfile.v2
   ```
   Keep the last 2–3 versions; A/B test in NetSeek/QuizVerse before retiring older ones.

4. **Evaluating before promoting:** run [`fine_tuning/evaluate.py`](evaluate.py) against a held-out test set. Don't switch the production env var (`SMARTSTUDY_MODEL_GENERAL`) to a new version that scored worse.

There's no built-in "auto-retrain on new data" loop — Kaggle T4 hours are limited and burning them on every dataset change is wasteful. Manual cadence is correct.

---

## 10. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| "transcript fetch failed" | Video deleted / private / no captions | Pipeline skips and continues. Check the recipe's video IDs. |
| All exam outputs return None | `max_tokens` too small | Already bumped to 4000 in `make_exam_pair` — bump higher if Putnam/IMO still fail |
| `JSONDecodeError` floods the log | Gemma producing malformed JSON | The lenient parser in `core/gemma_engine.py` handles markdown fences + LaTeX. If you see this, the parser has a new edge case — open an issue |
| GitHub clone times out | Repo too large or network issue | The connector has a 120s timeout and `--depth 1`. Try a smaller subdir via `"subdir": "..."` |
| Out of memory on Kaggle | T4 has 16 GB | Use 4-bit quantized base, smaller LoRA rank, `gradient_accumulation_steps=8` |
| Trained model still hallucinates | SFT data too small | Need more grounded `qa` pairs. Aim for **at least 500 `qa` examples** in the merged dataset before promoting |

---

## 11. Your concrete checklist (TL;DR)

- [ ] Verify YouTube IDs in the recipes you care about (run a tiny build first)
- [ ] Add 3–5 of your own recipes (different subjects)
- [ ] Run the master builder overnight: `.venv/bin/python3 fine_tuning/build_master_dataset.py`
- [ ] Sanity-check: `wc -l fine_tuning/datasets/master_sft.jsonl` should be **at least 200** before training
- [ ] Push dataset to Kaggle, run Stage 1 (SFT)
- [ ] Eval, then Stage 2 (GRPO) on quiz reward, then Stage 3 (SimPO)
- [ ] Export GGUF, `ollama create`, set env var, restart apps
- [ ] Compare with baseline on `evaluate.py`. Promote only if better.
