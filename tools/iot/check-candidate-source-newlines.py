#!/usr/bin/env python3
"""Reject platform-dependent text output in the recovery/peer generator graph.

Metadata JSON/log writers do not affect the reviewed driver-byte pins.
"""
import ast
from pathlib import Path
import re


def implicit_writers(tree):
    issues = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == 'write_text'):
            continue
        if any(keyword.arg == 'newline' and isinstance(keyword.value, ast.Constant)
               and keyword.value.value in ('', '\n', '\r', '\r\n')
               for keyword in node.keywords):
            continue
        target = ast.unparse(node.func.value)
        if '.json' in target or '.log' in target or target in ('report', 'manifest', 'output_manifest'):
            continue
        issues.append(node.lineno)
    return issues


def main():
    # Boundary fixtures: a source writer must specify its policy; metadata is
    # outside driver-byte identity. This check does not execute generated code.
    assert implicit_writers(ast.parse("path.write_text(source)")) == [1]
    assert implicit_writers(ast.parse("path.write_text(source, newline=None)")) == [1]
    assert not implicit_writers(ast.parse("path.write_text(source, newline='\\n')"))
    assert not implicit_writers(ast.parse("Path('manifest.json').write_text(data)"))
    root = Path(__file__).resolve().parent
    pending = ['prepare-current-recovery-chain.py', 'prepare-peer-retirement-chain.py']
    seen = set()
    issues = []
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        seen.add(name)
        tree = ast.parse((root / name).read_text(encoding='utf-8'))
        issues.extend(name + ':' + str(line) for line in implicit_writers(tree))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                    and re.fullmatch(r'[\w-]+\.py', node.value)
                    and (root / node.value).is_file()):
                pending.append(node.value)
    if issues:
        raise SystemExit('Platform-dependent candidate source writers: ' + ', '.join(issues))
    print('PASS explicit candidate source newlines in ' + str(len(seen)) + ' generator dependencies')


if __name__ == '__main__':
    main()
