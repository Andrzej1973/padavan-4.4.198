#!/usr/bin/env python3
"""Inventory MT7603 terminal-stop source contracts; never certify quiescence."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def function(source, signature):
    """Extract these vendor functions, whose closing brace starts a line."""
    if source.count(signature) != 1:
        raise ValueError('missing or ambiguous function: ' + signature)
    start = source.index(signature)
    end = source.index('\n}', start) + 2
    return source[start:end]


def audit(root):
    paths = ['chips/mt7603.c', 'hw_ctrl/cmm_asic_mt.c',
             'common/cmm_mac_pci.c', 'common/rtmp_init.c',
             'include/rtmp_chip.h', 'include/mac/mac_mt/mt_mac_pci.h']
    raw = {name: (root / name).read_bytes() for name in paths}
    sources = {name: data.decode() for name, data in raw.items()}
    chip = sources['chips/mt7603.c']
    mt = sources['hw_ctrl/cmm_asic_mt.c']
    observations = {}
    # Recognize only the reviewed source shapes. Changed code is UNKNOWN,
    # never automatically promoted to a supported shutdown implementation.
    observations['mt7603_disable_tx_rx_hook_null'] = bool(re.search(
        r'\.DisableTxRx\s*=\s*NULL\s*,', chip))
    for direction in ('Rx', 'Tx'):
        body = function(mt, 'INT StopDma' + direction + '(')
        observations['stop_dma_' + direction.lower() + '_rejects_hif_mt'] = bool(
            re.search(r'if\s*\(pAd->chipCap.hif_type == HIF_MT\)\s*\{'
                      r'[^{}]*return 0;', body))
    dma = function(mt, 'INT AsicSetWPDMA(')
    write = dma.find('RTMP_IO_WRITE32(')
    observations['wpdma_success_without_postwrite_readback'] = (
        write >= 0 and 'RTMP_IO_READ32(' not in dma[write:]
        and 'return TRUE;' in dma[write:])
    disable = function(sources['common/cmm_mac_pci.c'],
                       'VOID RT28XXDMADisable(')
    observations['void_dma_disable_discards_result'] = bool(re.search(
        r'\{\s*AsicSetWPDMA\(pAd, PDMA_TX_RX, FALSE\);\s*\}', disable))
    wrapper = function(sources['common/rtmp_init.c'], 'VOID RTMPDisableRxTx(')
    observations['void_rx_tx_disable_calls_void_dma_disable'] = (
        'RT28XXDMADisable(pAd);' in wrapper)
    irq = sources['include/mac/mac_mt/mt_mac_pci.h']
    begin = irq.index('#define RTMP_ASIC_INTERRUPT_DISABLE(')
    end = irq.index('#define RTMP_ASIC_INTERRUPT_ENABLE(', begin)
    block = irq[begin:end]
    observations['irq_mask_write_without_readback_or_join'] = (
        'MT_INT_MASK_CSR, 0x0' in block
        and 'RTMP_IO_READ32' not in block
        and 'synchronize_irq' not in block and 'free_irq' not in block)
    return {
        'scope': 'MT7603 unpreprocessed source inventory; not target or runtime proof',
        'source_sha256': {name: hashlib.sha256(data).hexdigest()
                          for name, data in raw.items()},
        'observations': observations,
        'reviewed_shapes_match': all(observations.values()),
        'terminal_quiescence': 'unproven',
        'production_accepted': False,
        'runtime_verified': False,
        'required': ['fence all producers and re-enable paths',
                     'verified device-specific DMA/IRQ stop and bounded receipt',
                     'IRQ/tasklet/work/timer joins and exact owner retirement',
                     'separate inaccessible-device removal path'],
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    report = audit(args.candidate)
    # Exclusive creation preserves earlier evidence and source files.
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print('Terminal quiescence: unproven; reviewed source shapes:',
          report['reviewed_shapes_match'])
