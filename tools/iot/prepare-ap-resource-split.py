#!/usr/bin/env python3
"""Prepare AP resource separation; caller ordering is deliberately not bound yet."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def split(source):
    def span(signature):
        definitions = list(re.finditer(re.escape(signature) + r'[^;{}]*\)\s*\{', source))
        if len(definitions) != 1:
            raise ValueError('Expected one AP body: ' + signature)
        start = definitions[0].start()
        return start, source.index('\n}', start) + 2
    # Work backwards so the earlier AP shutdown body can be located afresh.
    start, end = span('static BOOLEAN wr_iot_ap_stop_body(')
    body = source[start:end]
    tails = []
    for macro, call in (('DOT11R_FT_SUPPORT', 'FT_Release(pAd);'),
                        ('DOT11V_WNM_SUPPORT', 'DMSTable_Release(pAd);')):
        old = '#ifdef ' + macro + '\n\t' + call + '\n#endif /* ' + macro + ' */'
        if body.count(old) != 1:
            raise ValueError('Unexpected AP stop resource tail: ' + macro)
        tails.append(old)
        body = body.replace(old, old.replace('\t' + call, '\tif (hardware) ' + call))
    source = source[:start] + body + source[end:]
    start, end = span('static BOOLEAN wr_iot_ap_shutdown_body(')
    body = source[start:end]
    marker = '#ifdef IGMP_SNOOP_SUPPORT'
    first = body.index(marker)
    last = body.index('\tDBGPRINT(RT_DEBUG_TRACE, ("<--- APShutdown')
    resources = body[first:last]
    if (resources.count('NdisFreeSpinLock(&pAd->MacTabLock);') != 0 or
            resources.count('/* MacTabLock remains valid for retained owners and reopen. */') != 1 or
            resources.count('NdisFreeSpinLock(&pAd->WdsTabLock);') != 1):
        raise ValueError('Unexpected AP shutdown lock retirement')
    body = body[:first] + 'if (hardware) {\n' + resources + '}\n' + body[last:]
    source = source[:start] + body + source[end:]
    # Raw destructor body only. It must not be called until an integrated
    # close executor has proved RX/IRQ joins and recorded single execution.
    release = ('\nstatic VOID wr_iot_ap_release_resource_body(RTMP_ADAPTER *pAd)\n{\n (void)pAd;\n' +
               '\n'.join(tails) + '\n' + resources + '}\n')
    if 'wr_iot_ap_release_resource_body(' in source:
        raise ValueError('AP resource split already present')
    return source[:start] + release + source[start:]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    if a.output.exists() or a.output.resolve() == a.source.resolve():
        p.error('Expected a new separate output file')
    before = a.source.read_text()
    after = split(before)
    a.output.write_text(after)
    a.output.with_suffix(a.output.suffix+'.json').write_text(json.dumps({
        'scope':'unbound AP resource separation only',
        'input_sha256':hashlib.sha256(before.encode()).hexdigest(),
        'output_sha256':hashlib.sha256(after.encode()).hexdigest(),
        'close_order_bound':False,'target_compiled':False,
        'runtime_verified':False},indent=2)+'\n')


if __name__ == '__main__':
    main()
