"""GitHub source — clones a repo and harvests lecture notes / handouts.

Many professors keep their lecture notes on GitHub:
- afshinea/stanford-cs-229-machine-learning  (Stanford CS229 cheatsheets)
- mit-pdos/6.S081-2020-labs                  (MIT OS class)
- yandexdataschool/Practical_RL              (Yandex DS school)
- karpathy/nn-zero-to-hero                   (Karpathy's NN course)

We pull .md / .tex / .txt files, skip binaries, cap document size.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

name = "github"

ALLOWED_EXTS = {".md", ".markdown", ".tex", ".txt", ".rst"}
MAX_FILE_BYTES = 200_000   # skip files larger than 200 KB
MIN_FILE_BYTES = 800       # skip empty stubs


def fetch(spec: dict) -> list[dict]:
    """spec = {"repo": "owner/name", "subject": "ML", "subdir": "optional/path", "max_files": 100}"""
    repo = spec.get("repo", "")
    if not repo:
        return []
    subject = spec.get("subject", "General")
    subdir = spec.get("subdir", "")
    max_files = int(spec.get("max_files", 100))   # cap per-repo to keep runtimes sane

    if not shutil.which("git"):
        print("  ✗ git not installed")
        return []

    docs: list[dict] = []
    with tempfile.TemporaryDirectory() as tmp:
        clone_path = Path(tmp) / "repo"
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", f"https://github.com/{repo}.git", str(clone_path)],
                check=True, capture_output=True, timeout=120,
            )
        except subprocess.CalledProcessError as exc:
            print(f"  ✗ clone failed: {exc.stderr.decode()[:200] if exc.stderr else exc}")
            return []
        except subprocess.TimeoutExpired:
            print(f"  ✗ clone timed out")
            return []

        scan_root = clone_path / subdir if subdir else clone_path
        if not scan_root.exists():
            print(f"  ✗ subdir not found: {subdir}")
            return []

        for path in scan_root.rglob("*"):
            if len(docs) >= max_files:
                break
            if not path.is_file():
                continue
            if path.suffix.lower() not in ALLOWED_EXTS:
                continue
            try:
                size = path.stat().st_size
            except OSError:
                continue
            if size < MIN_FILE_BYTES or size > MAX_FILE_BYTES:
                continue
            try:
                text = path.read_text(errors="ignore")
            except Exception:
                continue
            rel = path.relative_to(clone_path).as_posix()
            docs.append({
                "text": text,
                "title": f"{repo}/{rel}",
                "source_id": f"github:{repo}:{rel}",
                "source_kind": "lecture_notes",
                "meta": {"repo": repo, "path": rel, "subject": subject,
                         "url": f"https://github.com/{repo}/blob/main/{rel}"},
            })

    print(f"  ✓ {repo}: {len(docs)} note files")
    return docs
