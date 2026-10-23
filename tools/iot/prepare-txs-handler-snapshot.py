#!/usr/bin/env python3
"""Snapshot a Type-1 TxS handler before dropping its registration lock."""
import argparse
import hashlib
import json
from pathlib import Path


def replace_one(text: str, before: str, after: str) -> str:
    if text.count(before) != 1:
        raise SystemExit('Changed Type-1 handler anchor: ' + before[:100])
    return text.replace(before, after, 1)


parser = argparse.ArgumentParser()
parser.add_argument('candidate', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
root = args.candidate.resolve()
out = args.output.resolve()
if out.exists() or root == out or root in out.parents or out in root.parents:
    raise SystemExit('New separate output required')
source = root / 'tx_rx/txs.c'
before = source.read_bytes()
text = before.decode('utf-8').replace('\r\n', '\n')
signature = 'INT32 ParseTxSPacket(RTMP_ADAPTER *pAd, UINT32 Pid,'
if text.count(signature) != 1:
    raise SystemExit('Changed parser signature')
start = text.index(signature)
end = text.index('\n}', start) + 2
function = text[start:end]
function = replace_one(
    function, '\tTXS_TYPE *TxSType = NULL;\n',
    '\tTXS_TYPE *TxSType = NULL;\n\tTXS_HANDLER Handler;\n')
function = replace_one(
    function,
    '\t\t\t\tRTMP_SPIN_UNLOCK_IRQRESTORE(&TxSCtl->TxSTypePerPktTypeLock'
    '[PktType][PktSubType % TOTAL_PID_HASH_NUMS_PER_PKT_TYPE], &Flags);\n'
    '\t\t\t\tTxSType->TxSHandler(pAd, Data, Priv);',
    '\t\t\t\tHandler = TxSType->TxSHandler;\n'
    '\t\t\t\tRTMP_SPIN_UNLOCK_IRQRESTORE(&TxSCtl->TxSTypePerPktTypeLock'
    '[PktType][PktSubType % TOTAL_PID_HASH_NUMS_PER_PKT_TYPE], &Flags);\n'
    '\t\t\t\tHandler(pAd, Data, Priv);')
text = text[:start] + function + text[end:]
if source.read_bytes() != before:
    raise SystemExit('Input changed during preparation')
target = out / 'tx_rx/txs.c'
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(text, encoding='utf-8')
(out / 'manifest.json').write_text(json.dumps({
    'source_sha256': hashlib.sha256(before).hexdigest(),
    'output_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
    'type1_handler_snapshotted_under_lock': True,
    'callback_lifetime_proven': False,
    'target_compiled': False,
    'runtime_verified': False,
}, indent=2) + '\n', encoding='utf-8')
print('Staged Type-1 TxS handler snapshot before registration unlock')
