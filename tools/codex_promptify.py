#!/usr/bin/env python3
import argparse
import json
import shutil
import subprocess
from pathlib import Path

PROMPTIFIER_SYSTEM = """You are a senior software engineer who turns a raw, rushed user request into an excellent Antigravity task prompt.
Return ONLY valid JSON matching the provided schema. No extra text.
"""

PROMPTIFIER_INSTRUCTIONS = """Take the RAW REQUEST and produce:
- expanded_prompt: a complete Antigravity-ready prompt (include context assumptions, step-by-step expectations, explicit files/areas to inspect, and verification steps).
- difficulty: easy/medium/hard.
- antigravity_model_hint: pick a model name the user can select in Antigravity (prefer: Gemini 3 Flash for easy, Claude Sonnet 4.5 for medium, Claude Opus 4.5 (Thinking) for hard; adjust if needed).
- codex_review_model: a Codex model string (e.g. gpt-5.2 for hard reviews; gpt-5.1-codex-mini for quick).
- acceptance_criteria: bullet list.
- suggested_commands: concrete commands to run for verification (lint/tests/build).
- notes: risks, edge cases, rollback notes.

RAW REQUEST:
"""


def _resolve_codex_cmd(preferred: str) -> list[str]:
    """
    Returns a command list to invoke codex. Handles:
    - regular executables/cmd wrappers found via PATH
    - PowerShell-only installs (codex.ps1) by wrapping with powershell -File
    """
    # If user passed something explicit, try as-is first.
    if preferred:
        found = shutil.which(preferred)
        if found:
            preferred = found
    else:
        preferred = "codex"

    # Try direct resolution first
    direct = shutil.which(preferred)
    if direct:
        if direct.lower().endswith(".ps1"):
            return ["powershell", "-ExecutionPolicy", "Bypass", "-File", direct]
        return [direct]

    # Try common Windows npm shim names
    for name in ("codex.cmd", "codex.ps1"):
        found = shutil.which(name)
        if found:
            if name.endswith(".ps1"):
                return ["powershell", "-ExecutionPolicy", "Bypass", "-File", found]
            return [found]

    raise FileNotFoundError("Cannot find Codex CLI (codex). Ensure npm global bin is in PATH.")


def run_codex_exec(
    model: str,
    schema_path: Path,
    output_path: Path,
    user_prompt: str,
    codex_cmd: str
) -> None:
    # codex exec:
    # - default is read-only sandbox
    # - --output-schema enforces JSON structure
    # - -o writes only the final message to the given file
    cmd = _resolve_codex_cmd(codex_cmd) + [
        "exec",
        "--model",
        model,
        "--output-schema",
        str(schema_path),
        "-o",
        str(output_path),
        f"{PROMPTIFIER_SYSTEM}\n\n{PROMPTIFIER_INSTRUCTIONS}\n{user_prompt}\n",
    ]
    subprocess.run(cmd, check=True)


def _read_raw_request(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig").strip()
    except UnicodeDecodeError:
        # PowerShell Set-Content default is UTF-16; fallback keeps UX simple.
        return path.read_text(encoding="utf-16").strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, help="Path to file with raw request text")
    ap.add_argument("--schema", default=".agent/schemas/prompt.schema.json")
    ap.add_argument("--out", default=".agent/tmp/prompt.json")
    ap.add_argument("--model", default="gpt-5.1-codex-max")
    ap.add_argument("--codex-cmd", default="codex", help="Codex CLI command name or path")
    args = ap.parse_args()

    raw_path = Path(args.raw)
    schema_path = Path(args.schema)
    out_path = Path(args.out)

    raw_text = _read_raw_request(raw_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    run_codex_exec(
        args.model,
        schema_path,
        out_path,
        raw_text,
        args.codex_cmd
    )

    data = json.loads(out_path.read_text(encoding="utf-8"))
    print(
        f"[OK] Wrote {out_path} | difficulty={data['difficulty']} | ag_model={data['antigravity_model_hint']}"
    )


if __name__ == "__main__":
    main()
