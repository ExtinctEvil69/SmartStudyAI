"""Validate + dedupe the merged training dataset.

Walks all per-recipe `*_sft.jsonl` files, parses each line, drops:
  - invalid JSON
  - missing the `messages` key or wrong shape
  - exact duplicates (same user input + same model output)
  - near-duplicates (same user input + first 200 chars of output)

Writes the cleaned union to `fine_tuning/datasets/master_sft.jsonl`.

Usage:
    .venv/bin/python3 fine_tuning/validate_dataset.py
"""

from __future__ import annotations

import json
from pathlib import Path


def main():
    datasets = Path("fine_tuning/datasets")
    files = sorted(datasets.glob("*_sft.jsonl"))
    files = [f for f in files if not f.name.startswith("master_sft")]

    print(f"Validating {len(files)} per-recipe files...")

    seen: set[tuple[str, str]] = set()
    valid: list[str] = []
    invalid_json = 0
    bad_shape = 0
    duplicates = 0

    for f in files:
        for line_no, line in enumerate(open(f), 1):
            line = line.strip()
            if not line:
                continue
            try:
                ex = json.loads(line)
            except json.JSONDecodeError:
                invalid_json += 1
                continue

            msgs = ex.get("messages") if isinstance(ex, dict) else None
            if (not isinstance(msgs, list) or len(msgs) < 2
                    or not all(isinstance(m, dict) and "content" in m for m in msgs)):
                bad_shape += 1
                continue

            user_in = msgs[0].get("content", "")
            model_out = msgs[1].get("content", "")
            if not isinstance(user_in, str) or not isinstance(model_out, str):
                bad_shape += 1
                continue

            key = (user_in[:600].strip(), model_out[:300].strip())
            if key in seen:
                duplicates += 1
                continue
            seen.add(key)
            valid.append(json.dumps(ex))   # re-serialize for canonical form

    out = datasets / "master_sft.jsonl"
    with open(out, "w") as o:
        for v in valid:
            o.write(v + "\n")

    print(f"  ✓ valid:         {len(valid):>5}")
    print(f"  ✗ invalid JSON:  {invalid_json:>5}")
    print(f"  ✗ bad shape:     {bad_shape:>5}")
    print(f"  ✗ duplicates:    {duplicates:>5}")
    print(f"  → wrote {len(valid)} examples to {out} ({out.stat().st_size/1024:.1f} KB)")


if __name__ == "__main__":
    main()
