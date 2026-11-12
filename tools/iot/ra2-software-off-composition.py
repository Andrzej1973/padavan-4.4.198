"""Stage scoped ra2 software admission/queue stop through existing MBSS paths."""
from pathlib import Path


def compose(changes, source, local):
    result = dict(changes)
    source, local = Path(source), Path(local)
    name = 'ap/ap_mbss.c'
    text = result.get(name)
    if text is None:
        text = (source / name).read_text()
    include = '#include "rt_config.h"'
    if text.count(include) != 1 or 'ra2-software-off.h' in text:
        raise ValueError('Software OFF include anchor changed')
    text = text.replace(include, include + '\n#include "ra2-software-off.h"', 1)
    begin = text.index('INT32 MBSS_Open(PNET_DEV pDev)')
    end = text.index('\n}', begin) + 2
    opening = text[begin:end]
    # The prepared SDK owns BcnRingLock around beacon publication. Restore
    # queue capabilities before that lock to preserve the table/IRQ lock order.
    anchor = '\tRTMP_SEM_LOCK(&pAd->BcnRingLock);'
    if anchor not in opening:
        anchor = '#ifdef AIRPLAY_SUPPORT'
    if opening.count(anchor) != 1:
        raise ValueError('Software OPEN restore anchor changed')
    opening = opening.replace(anchor,
        '    if (!wr_iot_ra2_software_open(pAd,pDev)) return -1;\n\n' + anchor, 1)
    text = text[:begin] + opening + text[end:]
    # Prepared open rollback must close capabilities restored before beacon
    # publication. Both predecessor layouts place this hook before their lock.
    abort_signature = 'INT MBSS_AbortOpen(PNET_DEV pDev)'
    if abort_signature in text:
        begin = text.index(abort_signature)
        end = text.index('\n}', begin) + 2
        abort = text[begin:end]
        anchor = 'if (!wr_iot_bcn_revoke_and_drain(pAd, BssId))'
        if anchor not in abort:
            anchor = 'RTMP_SEM_LOCK(&pAd->BcnRingLock);'
        if abort.count(anchor) != 1:
            raise ValueError('Software OPEN rollback anchor changed')
        abort = abort.replace(anchor,
            '(void)wr_iot_ra2_software_stop(pAd,pDev);\n    '+anchor, 1)
        text = text[:begin] + abort + text[end:]
    begin = text.index('INT MBSS_Close(PNET_DEV pDev)')
    closing = text[begin:]
    anchor = '\tRTMP_OS_NETDEV_STOP_QUEUE(pDev);'
    if closing.count(anchor) != 1:
        raise ValueError('Software OFF admission anchor changed')
    closing = closing.replace(anchor, anchor +
        '\n if (wr_iot_ra2_software_stop(pAd,pDev)<0) return -1;', 1)
    result[name] = text[:begin] + closing
    name = 'ap/ap_data.c'
    text = result.get(name)
    if text is None:
        text = (source / name).read_text()
    begin = text.index('INT ApAllowToSendPacket(')
    anchor = '\tRTMP_QueryPacketInfo(pPacket, &PacketInfo, &pSrcBufVA, &SrcBufLen);'
    end = text.index('\n}', begin) + 2
    tail = text[begin:end]
    if tail.count(anchor) != 1:
        raise ValueError('Software OFF packet admission anchor changed')
    tail = tail.replace(anchor, '''    if (IS_MT7603(pAd) && pAd->ApCfg.BssidNum == 3 &&
        wdev == &pAd->ApCfg.MBSSID[2].wdev &&
        !pAd->ApCfg.MBSSID[2].bcn_buf.bBcnSntReq)
        return FALSE;
''' + anchor, 1)
    result[name] = text[:begin] + tail + text[end:]
    name = 'include/ra2-software-off.h'
    if name in result or (source / name).exists():
        raise ValueError('Software OFF already staged')
    result[name] = (local / 'ra2-software-off.h').read_text()
    return result
