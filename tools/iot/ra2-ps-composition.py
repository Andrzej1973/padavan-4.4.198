"""Local SDK ra2 PS queue retention using existing association and queue state."""
from pathlib import Path


def compose(changes, source, local):
    result = dict(changes)
    source, local = Path(source), Path(local)

    def replace(name, old, new):
        value = result.get(name)
        if value is None:
            value = (source / name).read_text()
        if value.count(old) != 1:
            raise ValueError('ra2 PS retention anchor changed in ' + name)
        result[name] = value.replace(old, new, 1)

    for name, include in [('ap/ap.c', '#include "rt_config.h"'),
                          ('tx_rx/txs.c', '#include\t"rt_config.h"')]:
        replace(name, include, include + '\n#include "ra2-ps-retain.h"')
    old = '\t\t\t\tif (tr_entry->PsQIdleCount > 2)\n\t\t\t\t{'
    new = '''				if (tr_entry->PsQIdleCount > 2 &&
                    wr_iot_ra2_sleeping_pending(pAd,pEntry->wcid))
                {
                    /* Keep the owned PS queue for the normal wake/PS-Poll path.
                     * The periodic beacon builder consumes this live bitmap. */
                    tr_entry->PsQIdleCount = 0;
                    WLAN_MR_TIM_BIT_SET(pAd,2,pEntry->Aid);
                }
                else if (tr_entry->PsQIdleCount > 2)
                {'''
    replace('ap/ap.c', old, new)
    replace('tx_rx/txs.c',
            'INT32 PsDataTxSHandler(RTMP_ADAPTER *pAd, CHAR *Data, UINT32 Priv)\n{\n\tTXS_STRUC *txs_entry = (TXS_STRUC *)Data;\n\tTXS_D_3 *txs_d3 = &txs_entry->txs_d3;\n ',
            'INT32 PsDataTxSHandler(RTMP_ADAPTER *pAd, CHAR *Data, UINT32 Priv)\n{\n\tTXS_STRUC *txs_entry;\n\tTXS_D_3 *txs_d3;\n\n'
            '\tif (!pAd || !Data) return 0;\n'
            '\ttxs_entry = (TXS_STRUC *)Data;\n'
            '\ttxs_d3 = &txs_entry->txs_d3;\n ')
    replace('tx_rx/txs.c', '\tif (pAd->MacTab.tr_entry[txs_d3->wlan_idx].PsDeQWaitCnt) {', '''
    if (wr_iot_ra2_sleeping_pending(pAd,txs_d3->wlan_idx)) {
        /* Completion has no packet pointer or DMA ring-slot ownership.
         * Preserve the queued-data indication for the existing beacon path. */
        WLAN_MR_TIM_BIT_SET(pAd,2,pAd->MacTab.Content[txs_d3->wlan_idx].Aid);
#ifdef WR_IOT_PSM_DIAG
        /* LE is a delivered lifetime-error report. Attribute only current
         * association state; this is not a DMA/RF retirement receipt. */
        if (txs_entry->txs_d0.LE)
            wr_iot_ps_diag(6,2,txs_d3->wlan_idx,
                pAd->MacTab.tr_entry[txs_d3->wlan_idx].PsQIdleCount,
                pAd->MacTab.tr_entry[txs_d3->wlan_idx].enqCount);
#endif
    }
    /* Periodic SDK timeout owns ra2 PS-Poll pacing. Delayed reports cannot
     * acknowledge a newer poll or acquire ownership of its queued packet. */
    if (wr_iot_ra2_station(pAd,txs_d3->wlan_idx)) return 0;
	if (pAd->MacTab.tr_entry[txs_d3->wlan_idx].PsDeQWaitCnt) {''')
    # ra2 uses the existing periodic PS-Poll timeout, so its frames retain
    # their ordinary packet PID. Avoid creating PS-data completion dependencies.
    decisions = [
        ('ap/ap_data.c',
         'if (pTxBlk->tr_entry && pTxBlk->tr_entry->PsDeQWaitCnt)',
         'if (pTxBlk->tr_entry && pTxBlk->tr_entry->PsDeQWaitCnt &&\n'
         '            !wr_iot_ra2_station(pAd,pTxBlk->tr_entry->wcid))'),
        ('common/cmm_data.c',
         'if (pMacEntry && pAd->MacTab.tr_entry[wcid].PsDeQWaitCnt)',
         'if (pMacEntry && pAd->MacTab.tr_entry[wcid].PsDeQWaitCnt &&\n'
         '            !wr_iot_ra2_station(pAd,wcid))'),
        ('common/cmm_data_pci.c',
         'if (pMacEntry && pAd->MacTab.tr_entry[wcid].PsDeQWaitCnt)',
         'if (pMacEntry && pAd->MacTab.tr_entry[wcid].PsDeQWaitCnt &&\n'
         '            !wr_iot_ra2_station(pAd,wcid))'),
    ]
    for name, old, new in decisions:
        include = '#include\t"rt_config.h"' if name == 'common/cmm_data_pci.c' else '#include "rt_config.h"'
        replace(name, include, include + '\n#include "ra2-ps-retain.h"')
        replace(name, old, new)
    name = 'include/ra2-ps-retain.h'
    if name in result or (source / name).exists():
        raise ValueError('ra2 PS retention already present')
    result[name] = (local / 'ra2-ps-retain.h').read_text()
    return result
