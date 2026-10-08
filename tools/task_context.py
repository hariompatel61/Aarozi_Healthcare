
"""Print a compact context bundle for one Aarozi Healthcare task.
Usage: python tools/task_context.py .ai/tasks/P00-01-scope-freeze.md
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
if len(sys.argv) != 2:
    raise SystemExit("usage: python tools/task_context.py <task-file>")
path = root / sys.argv[1]
if not path.exists():
    raise SystemExit(f"task not found: {path}")
text = path.read_text(encoding="utf-8")
m = re.search(r"^## Context files\n(.*?)(?=^## )", text, flags=re.M|re.S)
if not m:
    raise SystemExit("no Context files section")
ctx = re.findall(r"^- `([^`]+)`$", m.group(1), flags=re.M)
print(f"# TASK CONTEXT: {sys.argv[1]}")
for rel in ctx:
    p = root / rel
    print(f"\n## {rel}\n")
    if not p.exists():
        print("[missing context file]")
        continue
    data = p.read_text(encoding="utf-8")
    if len(data) > 8000:
        data = data[:8000] + "\n...<truncated by context router>...\n"
    print(data)
