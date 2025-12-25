#!/usr/bin/env python3
import argparse
import json
import subprocess
from pathlib import Path

REVIEW_SYSTEM = (
    "You are a strict senior reviewer. Review the provided document and return ONLY JSON matching the schema. No extra text."
)
REVIEW_INSTRUCTIONS = """Review the Implementation Plan for:
- missing steps, wrong assumptions, risky migrations
- missing tests/verification
- unclear acceptance criteria
- dependency / environment pitfalls

If anything important is missing or unclear -> decision=revise with required_changes.
Otherwise approve.

DOCUMENT:
"""


import shutil

def _resolve_codex_cmd() -> list[str]:
    """
    Returns a command list to invoke codex. Handles:
    - regular executables/cmd wrappers found via PATH
    - PowerShell-only installs (codex.ps1) by wrapping with powershell -File
    """
    preferred = "codex"
    direct = shutil.which(preferred)
    if direct:
        if direct.lower().endswith(".ps1"):
            return ["powershell", "-ExecutionPolicy", "Bypass", "-File", direct]
        return [direct]

    for name in ("codex.cmd", "codex.ps1"):
        found = shutil.which(name)
        if found:
            if name.endswith(".ps1"):
                return ["powershell", "-ExecutionPolicy", "Bypass", "-File", found]
            return [found]

    raise FileNotFoundError("Cannot find Codex CLI (codex). Ensure npm global bin is in PATH.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", default="IMPLEMENTATION_PLAN.md")
    ap.add_argument("--schema", default=".agent/schemas/review.schema.json")
    ap.add_argument("--out", default=".agent/tmp/plan_review.json")
    ap.add_argument("--model", default="gpt-5.2")
    args = ap.parse_args()

    plan_path = Path(args.plan)
    schema_path = Path(args.schema)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    doc = plan_path.read_text(encoding="utf-8")
    print(f"DEBUG: Reviewing document of length {len(doc)}")

    cmd = _resolve_codex_cmd() + [
        "exec",
        "--model",
        args.model,
        "--output-schema",
        str(schema_path),
        "-o",
        str(out_path),
        f"{REVIEW_SYSTEM}\n\n{REVIEW_INSTRUCTIONS}\n{doc}\n",
    ]
    subprocess.run(cmd, check=True)

    data = json.loads(out_path.read_text(encoding="utf-8"))
    print(f"[OK] Plan review: {data['decision']}")


if __name__ == "__main__":
    main()
