#!/usr/bin/env python3
"""Restore per-request WSC IE state in the isolated feature-build driver."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def prepare(text):
    for name in ('ApCliEnqueueProbeRequest_A3Bcast', 'ApCliEnqueueProbeRequest'):
        definitions = list(re.finditer(r'static VOID ' + name + r'\([^;{}]*\)\s*\{', text))
        if len(definitions) != 1:
            raise ValueError('Expected one definition: ' + name)
        start = definitions[0].start()
        end = text.index('DBGPRINT(', start)
        prefix = text[start:end]
        old = '\t//BOOLEAN bHasWscIe = FALSE;'
        if prefix.count(old) != 1:
            raise ValueError('Unexpected WSC probe declaration: ' + name)
        replacement = '#ifdef WSC_AP_SUPPORT\n\tBOOLEAN bHasWscIe = FALSE;\n#endif'
        text = text[:start] + prefix.replace(old, replacement) + text[end:]
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('driver', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    path = args.driver / 'ap/apcli_sync.c'
    original = path.read_text()
    updated = prepare(original)
    path.write_text(updated)
    args.report.write_text(json.dumps({
        'scope': 'isolated WSC feature only',
        'source': 'ap/apcli_sync.c',
        'input_sha256': hashlib.sha256(original.encode()).hexdigest(),
        'output_sha256': hashlib.sha256(updated.encode()).hexdigest(),
        'production_installed': False,
        'runtime_verified': False,
    }, indent=2) + '\n')


if __name__ == '__main__':
    main()
