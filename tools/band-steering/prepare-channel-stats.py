#!/usr/bin/env python3
"""Expose the existing MT7603 non-QA steering counter-reset implementation."""
import argparse
import hashlib
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
root = p.parse_args().source
driver = root / 'trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3'
header = driver / 'include/band_steering.h'
data = header.read_bytes()
if hashlib.sha256(data).hexdigest() != '361eb9c7c2af3c63af1267d239bba6e3642b8717b7c0fae2df2e1f01807422db':
    raise ValueError('Pinned steering header changed; no files written')
qa = (driver / 'ate/include/qa_agent.h').read_text()
impl = (driver / 'hw_ctrl/cmm_asic_mt.c').read_text()
if '#define HQA_RX_RESET_PHY_COUNT                      0x9' not in qa:
    raise ValueError('Counter-reset identifier changed')
if '#ifndef CONFIG_QA\n#if defined(BAND_STEERING) || defined(CUSTOMER_DCC_FEATURE)' not in impl:
    raise ValueError('Existing non-QA implementation gate changed')
anchor = 'extern VOID EnableRadioChstats(PRTMP_ADAPTER \tpAd);'
text = data.decode()
if text.count(anchor) != 1:
    raise ValueError('Steering declaration anchor changed')
addition = ('/* Existing non-QA implementation in cmm_asic_mt.c; do not enable ATE/QA. */\n'
            '#ifndef CONFIG_QA\n'
            '#define HQA_RX_RESET_PHY_COUNT 0x9\n'
            'UINT32 AsicGetRxStat(RTMP_ADAPTER *pAd, UINT type);\n'
            '#endif\n')
with header.open('w', encoding='utf-8', newline='\n') as out:
    out.write(text.replace(anchor, addition + anchor))
print('Registered existing non-QA steering counter reset; full build verification pending')
