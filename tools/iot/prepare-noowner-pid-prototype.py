#!/usr/bin/env python3
"""Isolated allocator/parser experiment, NOT a deployable beacon lifecycle.

Input must already contain the checked allocator, callback ledger and claimed
slots. No TXD routing, DMA pacing, firmware or production workflow is changed.
Only a cold-start candidate can use this policy; never retrofit live slots.
"""
import argparse
import hashlib
import json
from pathlib import Path


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('No-owner PID anchor changed: ' + old[:70])
    return text.replace(old, new, 1)


def compose(source, header):
    if 'WR_IOT_NOOWNER_PID' in source or 'WR_IOT_NOOWNER_PID' in header:
        raise ValueError('No-owner policy already present')
    if source.count('INT32 AddTxSStatus(') != 1 or source.count('INT32 ParseTxSPacket(') != 1:
        raise ValueError('Ambiguous allocator/parser')
    if 'TXS_CLAIMED' not in source or 'WrTxSCompleteClaim' not in source:
        raise ValueError('Claimed-slot predecessor required')
    header = once(header, '#define TXS_STATUS_NUM 256',
                  '#define TXS_STATUS_NUM 256\n'
                  '/* Experimental non-owning wire PID, never a software slot. */\n'
                  '#define WR_IOT_NOOWNER_PID 255U')
    source = once(source, '\t\tpid = (UINT8)(TxSCtl->TxSPid + scan);\n',
                  '\t\tpid = (UINT8)(TxSCtl->TxSPid + scan);\n'
                  '\t\tif (pid == WR_IOT_NOOWNER_PID)\n\t\t\tcontinue;\n')
    # Before TxSValid diagnostics as well as slot lookup/callback accounting.
    start = source.index('INT32 ParseTxSPacket(')
    end = source.index('\n}', start) + 2
    parser = source[start:end]
    parser = once(parser, '\tif (TxSCtl->TxSValid == FALSE)',
                  '\t/* P has no software owner: late/duplicate P is inert. */\n'
                  '\tif (Pid == WR_IOT_NOOWNER_PID)\n\t\treturn 0;\n\n'
                  '\tif (TxSCtl->TxSValid == FALSE)')
    source = source[:start] + parser + source[end:]
    return source, header


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('candidate', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    root, out = a.candidate.resolve(), a.output.resolve()
    if out.exists() or root == out or root in out.parents or out in root.parents:
        raise SystemExit('New separate output required')
    names = ('tx_rx/txs.c', 'include/mac/mac_mt/mt_mac.h')
    before = [(root / n).read_bytes() for n in names]
    changed = compose(*(b.decode().replace('\r\n', '\n') for b in before))
    for n, b in zip(names, before):
        if (root / n).read_bytes() != b:
            raise SystemExit('Input changed during preparation')
    for n, text in zip(names, changed):
        path = out / n
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    report = {'wire_pid': 255, 'usable_software_slots': 255,
              'source_sha256': dict(zip(names, (hashlib.sha256(b).hexdigest() for b in before))),
              'output_sha256': {n: hashlib.sha256((out / n).read_bytes()).hexdigest() for n in names},
              'cold_start_only': True, 'txd_routing_implemented': False,
              'dma_pacing_implemented': False, 'rf_retirement_proven': False,
              'production_installed': False, 'target_compiled': False,
              'runtime_verified': False}
    (out / 'noowner-pid-prototype.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Staged isolated no-owner allocator/parser policy; no TXD routing or lifecycle fix')


if __name__ == '__main__':
    main()
