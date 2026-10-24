#!/usr/bin/env python3
"""Keep an accepted TxS PID unavailable until its parser path has exited."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def one(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise SystemExit('Changed TxS claim anchor: ' + old[:80])
    return text.replace(old, new, 1)


def function(text: str, signature: str) -> str:
    if text.count(signature) != 1:
        raise SystemExit('Changed TxS function: ' + signature)
    start = text.index(signature)
    return text[start:text.index('\n}', start) + 2]


parser = argparse.ArgumentParser()
parser.add_argument('candidate', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
root = args.candidate.resolve()
out = args.output.resolve()
if out.exists() or root == out or root in out.parents or out in root.parents:
    raise SystemExit('New separate output required')
txs_path = root / 'tx_rx/txs.c'
header_path = root / 'include/mac/mac_mt/mt_mac.h'
originals = {txs_path: txs_path.read_bytes(), header_path: header_path.read_bytes()}
txs = originals[txs_path].decode('utf-8').replace('\r\n', '\n')
header = originals[header_path].decode('utf-8').replace('\r\n', '\n')

header = one(header, '\tTXS_UNUSED,\n\tTXS_USED,',
             '\tTXS_UNUSED,\n\tTXS_USED,\n\tTXS_CLAIMED,')
add_sig = 'INT32 AddTxSStatus(RTMP_ADAPTER *pAd, UINT8 Type,'
add = function(txs, add_sig)
add = one(add,
          'if (TxSCtl->TxSStatus[pid].State != TXS_USED)',
          'if (TxSCtl->TxSStatus[pid].State == TXS_UNUSED)')
txs = one(txs, function(txs, add_sig), add)

remove_sig = 'INT32 RemoveTxSStatus(RTMP_ADAPTER *pAd, UINT8 TxSPid,'
remove = function(txs, remove_sig)
remove = one(remove,
             'TxSCtl->TxSStatus[TxSPid].State = TXS_UNUSED;',
             'TxSCtl->TxSStatus[TxSPid].State = TXS_CLAIMED;')
txs = one(txs, function(txs, remove_sig), remove)

complete = '''static INT32 WrTxSCompleteClaim(RTMP_ADAPTER *pAd, UINT8 Pid)
{
    TXS_CTL *ctl = &pAd->TxSCtl;
    ULONG flags;
    INT32 result = 0;

    RTMP_SPIN_LOCK_IRQSAVE(&ctl->TxSStatusLock, &flags);
    if (ctl->TxSStatus[Pid].State != TXS_CLAIMED) {
        ctl->BeaconCallbackAccountingFault = TRUE;
        result = -1;
    } else {
        ctl->TxSStatus[Pid].State = TXS_UNUSED;
    }
    RTMP_SPIN_UNLOCK_IRQRESTORE(&ctl->TxSStatusLock, &flags);
    return result;
}

'''
parse_sig = 'INT32 ParseTxSPacket(RTMP_ADAPTER *pAd, UINT32 Pid,'
parse = function(txs, parse_sig)
parse = one(parse,
            'RTMP_SPIN_UNLOCK_IRQRESTORE(&TxSCtl->TxSTypePerPktLock[PktPid % TOTAL_PID_HASH_NUMS], &Flags);\n'
            '                        return -1;',
            'RTMP_SPIN_UNLOCK_IRQRESTORE(&TxSCtl->TxSTypePerPktLock[PktPid % TOTAL_PID_HASH_NUMS], &Flags);\n'
            '\t\t\tWrTxSCompleteClaim(pAd, (UINT8)Pid);\n'
            '                        return -1;')
parse, count = re.subn(
    r'(\t\t\t\tRTMP_SPIN_UNLOCK_IRQRESTORE\(&TxSCtl->TxSTypePerPktLock'
    r'\[PktPid % TOTAL_PID_HASH_NUMS\],\s*&Flags\);\n)\t\t\t\treturn 0;',
    r'\g<1>\t\t\t\treturn WrTxSCompleteClaim(pAd, (UINT8)Pid);', parse)
if count != 1:
    raise SystemExit('Changed Type0 TxS success exit')
parse = one(parse,
            'wr_beacon_txs_callback_done(pAd, Type, PktType, PktSubType, Priv);\n'
            '                        return -1;',
            'wr_beacon_txs_callback_done(pAd, Type, PktType, PktSubType, Priv);\n'
            '\t\t\tWrTxSCompleteClaim(pAd, (UINT8)Pid);\n'
            '                        return -1;')
parse = one(parse,
            'wr_beacon_txs_callback_done(pAd, Type, PktType, PktSubType, Priv);\n'
            '\t\t\t\treturn 0;',
            'wr_beacon_txs_callback_done(pAd, Type, PktType, PktSubType, Priv);\n'
            '\t\t\t\treturn WrTxSCompleteClaim(pAd, (UINT8)Pid);')
parse = one(parse,
            '\treturn -1;\n}',
            '\tWrTxSCompleteClaim(pAd, (UINT8)Pid);\n\treturn -1;\n}')
if parse.count('WrTxSCompleteClaim(pAd, (UINT8)Pid)') != 5:
    raise SystemExit('Not all post-claim parser exits complete')
txs = one(txs, function(txs, parse_sig), complete + parse)
query_sig = 'INT32 WrBeaconTxSOutstanding(RTMP_ADAPTER *pAd, UINT32 BssId)'
query = function(txs, query_sig)
query = one(query,
            'status->State == TXS_USED && status->Type == TXS_TYPE1',
            'status->State != TXS_UNUSED && status->Type == TXS_TYPE1')
txs = one(txs, function(txs, query_sig), query)

for path, before in originals.items():
    if path.read_bytes() != before:
        raise SystemExit('Input changed during preparation')
for relative, content in (('tx_rx/txs.c', txs),
                          ('include/mac/mac_mt/mt_mac.h', header)):
    target = out / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding='utf-8')
manifest = {
    'source_sha256': {path.relative_to(root).as_posix(): hashlib.sha256(data).hexdigest()
                      for path, data in originals.items()},
    'output_sha256': {relative: hashlib.sha256((out / relative).read_bytes()).hexdigest()
                      for relative in ('tx_rx/txs.c', 'include/mac/mac_mt/mt_mac.h')},
    'claimed_slot_staged': True,
    'late_report_after_reuse_safe': False,
    'target_compiled': False,
    'runtime_verified': False,
}
(out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n',
                                   encoding='utf-8')
print('Staged claimed TxS slot until parser completion; no late-report proof')
