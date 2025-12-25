#!/usr/bin/env python3
import argparse
import json
import shutil
import subprocess
from pathlib import Path

REVIEW_SYSTEM = "You are a strict code reviewer. Return ONLY JSON matching the schema. No extra text."
REVIEW_INSTRUCTIONS = """Review the patch and test output for:
- correctness, edge cases, regressions
- style/maintainability issues
- missing tests
- security/safety concerns
If anything important remains -> revise with required_changes, else approve.
"""

def _resolve_codex_cmd(preferred: str) -> list[str]:
    if preferred:
        found = shutil.which(preferred)
        if found:
            preferred = found
    else:
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
    raise FileNotFoundError("Cannot find Codex CLI")


def git_diff() -> str:
    # Mostra tutto quello che è cambiato rispetto a HEAD (sia staged che unstaged)
    result = subprocess.run(["git", "diff", "HEAD"], capture_output=True, text=True)
    diff = result.stdout

    # Aggiungiamo i file nuovi untracked
    untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], capture_output=True, text=True)
    for f in untracked.stdout.splitlines():
        if f.endswith(".py"):
            content = read_optional(Path(f))
            if content:
                diff += f"\n\n--- NEW FILE: {f} ---\n{content}"

    return diff


def read_optional(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="utf-16")
        except Exception:
            return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schema", default=".agent/schemas/review.schema.json")
    ap.add_argument("--out", default=".agent/tmp/impl_review.json")
    ap.add_argument("--model", default="gpt-5.2-codex-max")
    ap.add_argument("--testlog", default=".agent/tmp/test_output.txt")
    ap.add_argument("--codex-cmd", default="codex")
    args = ap.parse_args()

    schema_path = Path(args.schema)
    out_path = Path(args.out)
    testlog_path = Path(args.testlog)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    diff = git_diff()
    testlog = read_optional(testlog_path)

    payload = f"""{REVIEW_SYSTEM}

{REVIEW_INSTRUCTIONS}
{diff}

TEST OUTPUT (if any):
{testlog}
"""

    cmd = _resolve_codex_cmd(args.codex_cmd) + [
        "exec",
        "--model",
        args.model,
        "--output-schema",
        str(schema_path),
        "-o",
        str(out_path),
    ]
    subprocess.run(cmd, input=payload, check=True, text=True, encoding="utf-8")

    data = json.loads(out_path.read_text(encoding="utf-8"))
    print(f"[OK] Impl review: {data['decision']}")
    print(f"Summary: {data['summary']}")
    if data['required_changes']:
        print("Required Changes:")
        for c in data['required_changes']:
            print(f"- {c}")


if __name__ == "__main__":
    main()
