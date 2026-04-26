# Polaris — Sunday Summary

**Generated:** 2026-04-26T02:52:00.225058

## Final dataset

- File: `fine_tuning/datasets/master_sft.jsonl`
- Examples: **3,226**
- Size: **22225.5 KB**

## Per-recipe yields

| Recipe | Examples |
|---|---:|
| d2l_deep_learning | 611 |
| neetcode_solutions_repo | 604 |
| ml_for_beginners | 356 |
| the_algorithms_python | 345 |
| ossu_computer_science | 181 |
| veritasium_physics | 109 |
| neetcode_leetcode | 106 |
| computerphile_cs | 91 |
| statquest_stats | 82 |
| numberphile_math | 73 |
| mit_1806_linear_algebra | 66 |
| stanford_cs229_cheatsheets | 66 |
| crashcourse_general | 60 |
| 3b1b_neural_networks | 59 |
| fireship_dev | 52 |
| harvard_cs50 | 52 |
| mit_6006_algorithms | 50 |
| stanford_cs229_ml | 50 |
| handson_ml3 | 46 |
| stanford_cs230_dl_cheatsheets | 42 |
| 3b1b_calculus | 41 |
| 3b1b_linear_algebra | 28 |
| mit_1801_calculus | 25 |
| mit_801_physics | 22 |
| karpathy_nn_zero_to_hero | 9 |

## Output-format distribution (heuristic)

| Format | Count | % |
|---|---:|---:|
| prose | 1594 | 49.4% |
| quiz_json | 661 | 20.5% |
| markdown_doc | 627 | 19.4% |
| exam_json | 277 | 8.6% |
| agent_plan | 67 | 2.1% |

## Sample inputs (first 3)

- You are a study coach. Create a concise learning plan.  Goal: Master 3B1B — Essence of Calculus, Ch.1 (Mathematics) for a college-level exam
- Use only the source below.  According to the text, how does the process of approximating the area of a circle by slicing it into concentric 
- Generate a 3-question quiz from this source. Topic: 3B1B — Essence of Calculus, Ch.1  Hey everyone, Grant here. This is the first video in a

## Ready for Kaggle?

✅ **YES** — 3,226 valid examples is well above the 500 threshold for meaningful Stage 1 SFT.

## Next steps (Wednesday)

1. Push `master_sft.jsonl` to Kaggle Dataset or GitHub gist
2. Open `notebooks/gemma4_finetune.ipynb`
3. Stage 1 SFT (~3h on T4)
4. Stage 2 GRPO (~3h)
5. Stage 3 SimPO (~2h)
6. Export GGUF + `ollama create polaris-edu`
7. A/B test before promoting to production env vars
