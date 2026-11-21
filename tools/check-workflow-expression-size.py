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
            # Keep headroom for GitHub's expression conversion/escaping.
            # Raw scalar length alone missed the 124d2da validation failure.
            if len(value) >= 19000:
                raise SystemExit(f'{path.relative_to(root)}:{index + 1}: '
                                 f'expression-bearing run is {len(value)} characters (budget 19000)')
# Zero is valid when all large steps use external scripts and env inputs.
print(f'PASS {checked} expression-bearing workflow run blocks below 19000-character budget')
