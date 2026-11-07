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


def brace_wsc(text, crypto=False):
    replacements = [
        ('    if (*pBI != NULL)\n        BigInteger_Free(pBI);',
         '    if (*pBI != NULL) {\n        BigInteger_Free(pBI);\n    }', 1)
    ] if crypto else [
        ('    if (Id == pWpsCtrl->lastId)\n        Id += 1;',
         '    if (Id == pWpsCtrl->lastId) {\n        Id += 1;\n    }', 1),
        ('    if(pOutBuffer == NULL)\n        return;',
         '    if(pOutBuffer == NULL) {\n        return;\n    }', 3),
        ('    if (bFromUPnP)\n        WscStop(pAd, FALSE, pWscControl);',
         '    if (bFromUPnP) {\n        WscStop(pAd, FALSE, pWscControl);\n    }', 1),
    ]
    for old, new, count in replacements:
        if text.count(old) != count:
            raise ValueError('Unexpected WSC conditional: ' + old)
        text = text.replace(old, new)
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('driver', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    path = args.driver / 'ap/apcli_sync.c'
    original = path.read_text()
    updated = prepare(original)
    changes = {'ap/apcli_sync.c': (original, updated)}
    for relative, crypto in (('common/wsc.c', False), ('common/crypt_biginteger.c', True)):
        original_feature = (args.driver / relative).read_text()
        changes[relative] = (original_feature, brace_wsc(original_feature, crypto))
    # Validate every expected source anchor before changing any file.
    for relative, (_, prepared) in changes.items():
        (args.driver / relative).write_text(prepared)
    args.report.write_text(json.dumps({
        'scope': 'isolated WSC feature only',
        'source': 'ap/apcli_sync.c',
        'input_sha256': hashlib.sha256(original.encode()).hexdigest(),
        'output_sha256': hashlib.sha256(updated.encode()).hexdigest(),
        'changed_sources': {name: {
            'input_sha256': hashlib.sha256(before.encode()).hexdigest(),
            'output_sha256': hashlib.sha256(after.encode()).hexdigest(),
        } for name, (before, after) in changes.items()},
        'production_installed': False,
        'runtime_verified': False,
    }, indent=2) + '\n')


if __name__ == '__main__':
    main()
