"""
Reports the size and cache-stability of the OKF system prompt built from the real corpus.

The point of the optimisation is prompt structure, not retrieval: the knowledge block must be
byte-identical across requests and languages so the model can serve it from cache. This script
measures the block, checks that invariant, and reports what frontmatter stripping saved.

Usage (from backend/):
    DATA_DIR=../data MANIFEST_PATH=../data/manifest.json python scripts/bench_prompt.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

os.environ.setdefault("DATA_DIR", str(Path(__file__).parent.parent.parent / "data"))
os.environ.setdefault("MANIFEST_PATH", str(Path(__file__).parent.parent.parent / "data" / "manifest.json"))

from lck_backend.knowledge.snapshot import SnapshotManager, strip_frontmatter  # noqa: E402
from lck_backend.strategies.okf import OKF_KNOWLEDGE_TEMPLATE, OKF_LANGUAGE_TEMPLATE  # noqa: E402


def approx_tokens(text: str) -> int:
    """Rough proxy: ~4 chars per token. Good enough for a before/after comparison."""
    return round(len(text) / 4)


def main() -> int:
    manager = SnapshotManager()
    snapshot = manager.create_snapshot()

    context = snapshot.get_full_context()
    prefix = OKF_KNOWLEDGE_TEMPLATE.format(context=context)

    # What the prompt would have been without stripping.
    data_dir = Path(os.environ["DATA_DIR"])
    raw_chars = sum(
        (data_dir / doc.source).read_text(encoding="utf-8").__len__()
        for doc in snapshot.manifest.documents
        if doc.enabled
    )
    stripped_chars = sum(len(c) for c in snapshot.documents_content.values())

    print(f"snapshot            : {snapshot.version}")
    print(f"documents           : {len(snapshot.documents_content)}")
    print(f"chunks              : {len(snapshot.chunks)}")
    print()
    print(f"corpus before strip : {raw_chars:,} chars  (~{approx_tokens('x' * raw_chars):,} tokens)")
    print(f"corpus after strip  : {stripped_chars:,} chars  (~{approx_tokens('x' * stripped_chars):,} tokens)")
    print(f"frontmatter removed : {raw_chars - stripped_chars:,} chars")
    print()
    print(f"cacheable prefix    : {len(prefix):,} chars  (~{approx_tokens(prefix):,} tokens)")
    for lang in ("en", "hi", "es"):
        tail = OKF_LANGUAGE_TEMPLATE.format(language_instruction=lang)
        print(f"  volatile tail {lang}   : {len(tail):,} chars")

    # Invariants the optimisation depends on.
    checks = {
        "prefix carries no language directive": "Respond in" not in prefix,
        "no YAML fences leaked into prompt": "\n---\nid:" not in prefix,
        "no stale nia_airport paths in prompt": "nia_airport" not in prefix,
        "context memoised per snapshot": snapshot.get_full_context() is context,
    }
    print()
    for label, ok in checks.items():
        print(f"[{'PASS' if ok else 'FAIL'}] {label}")

    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
