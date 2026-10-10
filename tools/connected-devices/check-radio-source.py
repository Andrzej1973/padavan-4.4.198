#!/usr/bin/env python3
"""Check pinned station field semantics; target layout still needs compilation."""
import argparse
import re
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
a = p.parse_args()
def fields(path):
    text = path.read_text(encoding='utf-8')
    body = re.search(r'typedef struct _RT_802_11_MAC_ENTRY\s*\{(.*?)\}', text, re.S).group(1)
    body = re.sub(r'/\*.*?\*/', '', body, flags=re.S)
    body = re.sub(r'//[^\n]*', '', body)
    for old, new in [('UCHAR', 'unsigned char'), ('CHAR', 'char'), ('UINT32', 'unsigned int'), ('MAC_ADDR_LEN', 'ETHER_ADDR_LEN')]:
        body = re.sub(r'\b' + old + r'\b', new, body)
    return re.sub(r'\s+', '', body)
expected = fields(a.source / 'trunk/user/shared/include/ralink_priv.h')
for radio in ('mt76x2', 'mt76x3'):
    root = a.source / 'trunk/linux-4.4.x/drivers/net/wireless/mediatek' / radio
    assert fields(root / 'include/oid.h') == expected, radio
    text = (root / 'common/cmm_info.c').read_text(encoding='utf-8')
    body = text[text.index('VOID RTMPIoctlGetMacTable('):]
    body = body[:body.index('\nVOID ', 1)] if '\nVOID ' in body[1:] else body
    required = ['pEntry->Sst == SST_ASSOC', 'wrq->u.data.length = sizeof(RT_802_11_MAC_TABLE);']
    if radio == 'mt76x2':
        required += ['wrq->u.data.length = 0;', 'wrq_len < sizeof(RT_802_11_MAC_TABLE)', 'pDst->ApIdx = (UCHAR)pEntry->apidx;']
    else:
        required += ['pDst->ApIdx = (UCHAR)pEntry->func_tb_idx;']
    for evidence in required:
        assert evidence in body, (radio, evidence)
print('PASS both pinned drivers expose matching station fields and associated-client table semantics; target ABI/runtime unverified')
