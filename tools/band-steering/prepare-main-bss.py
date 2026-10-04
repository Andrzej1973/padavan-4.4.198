#!/usr/bin/env python3
"""Keep legacy MT76x2 steering admission and RSSI kicks on the main BSS only."""
import argparse
import hashlib
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
root = p.parse_args().source
driver = root / 'trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x2'
header = driver / 'include/band_steering.h'
source = driver / 'ap/ap_band_steering.c'
old_header = header.read_text()
old_source = source.read_text()
expected_header = 'f9ea2fb868c3fe32bdc2e7a98ed1b15e835aedbbd082eb45c689cbb850695503'
expected_sources = {
    '0a914a042f31419cc92da3ed51e5b642b4b6ec4ff9b3c656ec8c0973bad11a0c',
    '35ed4a20e91bbc6139e05267575e76c4908e4fdc851d7c5f2bdf9aaffc503460',
}
if (hashlib.sha256(header.read_bytes()).hexdigest() != expected_header or
        hashlib.sha256(source.read_bytes()).hexdigest() not in expected_sources):
    raise ValueError('Unrecognized pinned/prepared legacy sources; no files written')
call = '*_pRet = BndStrg_CheckConnectionReq('
body = '\tCHAR Rssi = RTMPAvgRssi(pAd, &pEntry->RssiSample);'
if old_header.count(call) != 1 or old_source.count(body) != 1:
    raise ValueError('Legacy admission/kick source anchors changed; no files written')
new_header = old_header.replace(call,
    '*_pRet = (!(_wdev) || (_wdev)->func_idx != MAIN_MBSSID) ? TRUE : BndStrg_CheckConnectionReq(')
new_source = old_source.replace(body,
    '\tCHAR Rssi;\n'
    '\t/* Guest networks must retain their independent admission and RSSI policy. */\n'
    '\tif (!pEntry || !pEntry->wdev || pEntry->wdev->func_idx != MAIN_MBSSID)\n'
    '\t\treturn TRUE;\n'
    '\tRssi = RTMPAvgRssi(pAd, &pEntry->RssiSample);')
report = {'runtime_verified': False, 'files': []}
for path, before, after in [(header, old_header, new_header), (source, old_source, new_source)]:
    with path.open('w', encoding='utf-8', newline='\n') as out:
        out.write(after)
    report['files'].append({'path': str(path.relative_to(root)),
        'before_sha256': hashlib.sha256(before.encode()).hexdigest(),
        'after_sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
(root / 'band-steering-main-bss-preparation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))

