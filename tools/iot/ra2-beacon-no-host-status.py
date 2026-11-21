"""Unbound experiment: suppress ra2 long-beacon TxS before PID allocation.

This is NOT a usable beacon lifecycle. The tracked submission guard must stay
installed until separate DMA ownership, natural-window pacing and OFF/reopen
integration are implemented. Never apply this transformation in production.
"""
from pathlib import Path

SIGNATURE = 'VOID write_tmac_info('
POLICY = '''!(IS_MT7603(pAd) && pAd->ApCfg.BssidNum == 3 &&
                    info->bss_idx == 2 && info->TxSPriv == 2 &&
                    txd_0->q_idx == Q_IDX_BCN &&
                    txd_2->frm_type == FC_TYPE_MGMT &&
                    txd_2->sub_type == SUBTYPE_BEACON)'''
ANCHOR = 'if (TxSCtl->TxS2HostStatusPerPktType[txd_2->frm_type] & (1 << txd_2->sub_type))'


def compose(source):
    """Change only the management constructor's TYPE1 host-status branch."""
    if source.count(SIGNATURE) != 1 or POLICY in source:
        raise ValueError('Expected one unchanged management TXD constructor')
    start = source.index(SIGNATURE)
    end = source.index('\n}', start) + 2
    body = source[start:end]
    if body.count(ANCHOR) != 1:
        raise ValueError('TYPE1 host-status policy anchor changed')
    position = body.index(ANCHOR)
    tail = body[position:]
    if ('AddTxSStatus(pAd, TXS_TYPE1' not in tail or
            'info->TxSPriv' not in tail or
            'txd_5->tx_status_2_host = 0;' not in tail or
            'info->TxSReservationGeneration = 0;' not in body):
        raise ValueError('Expected checked allocator and initialized reservation output')
    replacement = 'if (' + POLICY + ' &&\n                    (' + ANCHOR[4:-1] + '))'
    return source[:start] + body.replace(ANCHOR, replacement, 1) + source[end:]


def compose_periodic(source):
    """Unbound only: compose matching periodic path, preserving other helpers."""
    signature = 'static inline int wr_iot_bcn_periodic_ready('
    if source.count(signature) != 1 or 'AsicGetTsfTime(ad,&high,&low);' in source:
        raise ValueError('Expected unchanged tracked periodic path')
    start = source.index(signature)
    end = source.index('\n}', start) + 2
    body = source[start:end]
    if ('WrBeaconTxSOutstanding' not in body or 'BCN_TX_IDLE' not in body or
            'wr_iot_beacon_gate_submit' not in body):
        raise ValueError('Tracked periodic path changed')
    replacement = Path(__file__).with_name('ra2-beacon-periodic-experiment.inc').read_text()
    return source[:start] + replacement + source[end:]


def compose_builder_ticket(source, header):
    """Unbound internal ABI: copy the original wrapper ticket into submission.

    This does not authorize generation0 or modify any firmware descriptor.
    The pre-existing reservation is passed by value to lower submission.
    """
    signature = 'static VOID wr_iot_APUpdateBeaconFrame_inner(RTMP_ADAPTER *pAd, INT apidx)'
    producer_call = '\n   wr_iot_APUpdateBeaconFrame_inner(pAd, apidx);'
    legacy_call = '\n wr_iot_APUpdateBeaconFrame_inner(pAd, apidx);'
    assignment = 'reservation.generation = write_tmac_info_beacon('
    declaration = ('typedef struct _WR_BCN_TXS_RESERVATION {\n'
                   '\tUINT8 pid;\n\tUINT32 generation;\n'
                   '} WR_BCN_TXS_RESERVATION;')
    if (source.count(signature) != 1 or source.count(producer_call) != 1 or
            source.count(legacy_call) != 1 or source.count(assignment) != 1 or
            header.count(declaration) != 1 or
            source.count('wr_iot_APUpdateBeaconFrame_inner(') != 3):
        raise ValueError('Builder/reservation ABI or call sites changed')
    source = source.replace(signature, signature[:-1] +
                            ', const struct wr_iot_beacon_producer_ticket *producer)', 1)
    source = source.replace(producer_call, producer_call.replace('apidx);', 'apidx, &ticket);'), 1)
    source = source.replace(legacy_call, legacy_call.replace('apidx);', 'apidx, NULL);'), 1)
    source = source.replace(assignment,
                            'if (producer) reservation.producer = *producer;\n\t' + assignment, 1)
    header = header.replace(declaration,
                            '#include "beacon-producer-gate.h"\n' +
                            declaration.replace('\n} WR_',
                            '\n\tstruct wr_iot_beacon_producer_ticket producer;\n} WR_'), 1)
    return source, header


def compose_callback(source):
    """Unbound cold no-host mode: ra2 reports cannot mutate beacon state.

    This does not fix PID aliasing in the shared parser, establish a cold epoch
    or permit clearing its ledger. Main/Guest callback logic is unchanged.
    """
    signature = 'INT32 BcnTxSHandler(RTMP_ADAPTER *pAd, CHAR *Data, UINT32 Priv)'
    if source.count(signature) != 1 or 'Unrequested ra2 beacon status' in source:
        raise ValueError('Expected unchanged beacon callback')
    start = source.index(signature)
    end = source.index('\n}', start) + 2
    body = source[start:end]
    anchor = '\t\t\tbss_idx = (UCHAR)Priv;'
    lock = 'RTMP_IRQ_LOCK(&pAd->BcnRingLock, BcnFlags);'
    if (body.count(anchor) != 1 or body.count(lock) != 1 or
            body.index(lock) > body.index(anchor) or 'BCN_TX_STOP' not in body):
        raise ValueError('Expected locked bounds/STOP callback guards')
    guard = '''#if defined(MT7603) && defined(RTMP_MAC_PCI) && defined(MT_MAC)
\t\t\t/* Unrequested ra2 beacon status cannot advance a new lifecycle. */
\t\t\tif (IS_MT7603(pAd) && pAd->ApCfg.BssidNum == 3 && Priv == 2) {
\t\t\t\tRTMP_IRQ_UNLOCK(&pAd->BcnRingLock, BcnFlags);
\t\t\t\treturn -1;
\t\t\t}
#endif
'''
    return source[:start] + body.replace(anchor, guard + anchor, 1) + source[end:]
