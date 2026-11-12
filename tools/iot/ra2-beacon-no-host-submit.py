"""Unbound lower-submit composition for the reservation-free experiment.

Never install this fragment alone. It requires the original producer ticket
ABI, matching no-host constructor/pacing, and a separately established cold
mode/callback lifecycle. The production tracked guard remains unchanged.
"""
from pathlib import Path
import runpy

TRACKED = runpy.run_path(str(Path(__file__).with_name('tracked-beacon-reservation.py')))


def compose(source):
    start, end, body = TRACKED['selected'](source)
    if body.count(TRACKED['GUARD']) != 1 or body.count(TRACKED['LOCKED_GUARD']) != 1:
        raise ValueError('Expected unchanged tracked lower submission')
    if body.count('HAL_KickOutMgmtTx(') != 2 or 'goto unsubmitted;' not in body:
        raise ValueError('Expected checked MT PCI submit/rollback')
    early = '''
\t/* Unbound no-host mode accepts only the original builder producer. */
\tif (IS_MT7603(pAd) && pAd->chipCap.hif_type == HIF_MT && apidx == 2 &&
\t    (pAd->ApCfg.BssidNum != 3 || reservation.generation || reservation.pid ||
\t     !reservation.producer.active || !reservation.producer.generation))
\t\tgoto unsubmitted;
'''
    locked = '''
\t\tif (IS_MT7603(pAd) && pAd->chipCap.hif_type == HIF_MT && apidx == 2 &&
\t\t    !wr_iot_ra2_no_host_packet(pAd, pkt, &reservation.producer,
\t\t                               buf, len, wr_dma_snapshot)) {
\t\t\tRTMP_SEM_UNLOCK(&pAd->BcnRingLock);
\t\t\tgoto unsubmitted;
\t\t}
'''
    body = body.replace('{\n', '{\n\tint wr_dma_snapshot = -1;\n', 1)
    body = body.replace(TRACKED['GUARD'], early, 1)
    body = body.replace(TRACKED['LOCKED_GUARD'], locked, 1)
    lock = '\t\tRTMP_SEM_LOCK(&pAd->BcnRingLock);'
    if body.count(lock) != 1:
        raise ValueError('Submission lock changed')
    body = body.replace(lock,
        '\t\tif (IS_MT7603(pAd) && pAd->chipCap.hif_type == HIF_MT && apidx == 2)\n'
        '\t\t\twr_dma_snapshot = WrBeaconDmaOutstanding(pAd, 2);\n' + lock, 1)
    if not (body.index(early) < body.index('bcn_buf = &pAd->ApCfg.MBSSID') and
            body.index('WrBeaconDmaOutstanding(') < body.index(lock) <
            body.index('wr_iot_ra2_no_host_packet(') < body.index('HAL_KickOutMgmtTx(')):
        raise ValueError('Lower source ownership/check order changed')
    return (source[:start] + '#include "ra2-beacon-no-host-packet.h"\n' +
            body + source[end:])
