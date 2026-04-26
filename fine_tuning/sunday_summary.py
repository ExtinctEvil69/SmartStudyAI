"""Sunday summary — produces a final stats report for the training dataset."""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path


def main():
    datasets = Path("fine_tuning/datasets")
    master = datasets / "master_sft.jsonl"
    if not master.exists():
        print("master_sft.jsonl not found")
        return

    files = sorted(datasets.glob("*_sft.jsonl"))
    files = [f for f in files if not f.name.startswith("master_sft")]

    # Per-recipe yields
    yields = {f.stem.removesuffix("_sft"): sum(1 for _ in open(f)) for f in files}

    # Output-format distribution (rough heuristic on first 100 chars of model output)
    fmt_counts = Counter()
    total = 0
    sample_inputs: list[str] = []
    for line in open(master):
        line = line.strip()
        if not line:
            continue
        try:
            ex = json.loads(line)
        except json.JSONDecodeError:
            continue
        total += 1
        out = ex["messages"][1].get("content", "")
        head = out[:200].strip()
        if head.startswith("{") and '"questions"' in head[:300]:
            fmt_counts["quiz_json"] += 1
        elif head.startswith("{") and '"plan"' in head[:300]:
            fmt_counts["agent_plan"] += 1
        elif head.startswith("{") and '"problem"' in head[:300]:
            fmt_counts["exam_json"] += 1
        elif head.startswith("##") or head.startswith("# "):
            fmt_counts["markdown_doc"] += 1
        else:
            fmt_counts["prose"] += 1
        if total <= 3:
            sample_inputs.append(ex["messages"][0]["content"][:140].replace("\n", " "))

    # Write summary
    out_md = Path("reports/sunday_summary.md")
    out_md.parent.mkdir(parents=True, exist_ok=True)
    with open(out_md, "w") as f:
        f.write(f"# Polaris — Sunday Summary\n\n")
        f.write(f"**Generated:** {datetime.now().isoformat()}\n\n")
        f.write(f"## Final dataset\n\n")
        f.write(f"- File: `fine_tuning/datasets/master_sft.jsonl`\n")
        f.write(f"- Examples: **{total:,}**\n")
        f.write(f"- Size: **{master.stat().st_size/1024:.1f} KB**\n\n")
        f.write(f"## Per-recipe yields\n\n")
        f.write("| Recipe | Examples |\n|---|---:|\n")
        for r, n in sorted(yields.items(), key=lambda x: -x[1]):
            f.write(f"| {r} | {n} |\n")
        f.write(f"\n## Output-format distribution (heuristic)\n\n")
        f.write("| Format | Count | % |\n|---|---:|---:|\n")
        for fmt, n in fmt_counts.most_common():
            pct = 100 * n / total if total else 0
            f.write(f"| {fmt} | {n} | {pct:.1f}% |\n")
        f.write(f"\n## Sample inputs (first 3)\n\n")
        for s in sample_inputs:
            f.write(f"- {s}\n")
        f.write(f"\n## Ready for Kaggle?\n\n")
        if total >= 500:
            f.write(f"✅ **YES** — {total:,} valid examples is well above the 500 threshold for meaningful Stage 1 SFT.\n")
        else:
            f.write(f"⚠️ Only {total} examples. Consider adding more recipes before training.\n")
        f.write(f"\n## Next steps (Wednesday)\n\n")
        f.write(f"1. Push `master_sft.jsonl` to Kaggle Dataset or GitHub gist\n")
        f.write(f"2. Open `notebooks/gemma4_finetune.ipynb`\n")
        f.write(f"3. Stage 1 SFT (~3h on T4)\n")
        f.write(f"4. Stage 2 GRPO (~3h)\n")
        f.write(f"5. Stage 3 SimPO (~2h)\n")
        f.write(f"6. Export GGUF + `ollama create polaris-edu`\n")
        f.write(f"7. A/B test before promoting to production env vars\n")

    print(f"✓ wrote {out_md}")
    print(f"  total examples: {total:,}")
    print(f"  recipes: {len(yields)}")


if __name__ == "__main__":
    main()
