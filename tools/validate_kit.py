
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT/'.ai/task-manifest.json').read_text())
assert manifest['project'] == 'Aarozi Healthcare'
assert manifest['task_count'] == len(manifest['tasks'])
for task in manifest['tasks']:
    p = ROOT / task['file']
    assert p.exists(), p
    text = p.read_text()
    for section in ['## Objective','## Dependencies','## Context files','## Implementation prompt','## Test / verification','## Done criteria']:
        assert section in text, (task['id'], section)
print(f"OK: {manifest['task_count']} task files present and structured")
