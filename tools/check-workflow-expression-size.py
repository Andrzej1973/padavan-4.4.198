#!/usr/bin/env python3
"""Check expression-bearing run scalars against GitHub's observed size limit.

Dependency-free check for repository workflows using literal run blocks.
This is a focused size regression check, not a complete workflow validator.
"""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
checked = 0
for path in sorted((root / '.github/workflows').glob('*.yml')):
    lines = path.read_text().splitlines(keepends=True)
    for index, line in enumerate(lines):
        match = re.fullmatch(r'( *)run: *[|>]([-+]?)\s*\n?', line)
        if not match:
            continue
        indent = len(match[1])
        block = []
        for following in lines[index + 1:]:
            if following.strip() and len(following) - len(following.lstrip(' ')) <= indent:
                break
            block.append(following)
        nonempty = [len(s) - len(s.lstrip(' ')) for s in block if s.strip()]
        margin = min(nonempty, default=indent + 2)
        value = ''.join(s[margin:] if s.strip() else '\n' for s in block)
        if '${{' in value:
            checked += 1
            if len(value) >= 21000:
                raise SystemExit(f'{path.relative_to(root)}:{index + 1}: '
                                 f'expression-bearing run is {len(value)} characters (limit 21000)')
assert checked, 'No expression-bearing run blocks checked'
print(f'PASS {checked} expression-bearing workflow run blocks below 21000 characters')
