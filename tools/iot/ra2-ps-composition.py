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
    replace('tx_rx/txs.c', '\tif (pAd->MacTab.tr_entry[txs_d3->wlan_idx].PsDeQWaitCnt) {', '''
    if (wr_iot_ra2_sleeping_pending(pAd,txs_d3->wlan_idx)) {
        /* Completion has no packet pointer or timeout reason in this ABI.
         * Preserve the queued-data indication for the existing beacon path. */
        WLAN_MR_TIM_BIT_SET(pAd,2,pAd->MacTab.Content[txs_d3->wlan_idx].Aid);
    }
	if (pAd->MacTab.tr_entry[txs_d3->wlan_idx].PsDeQWaitCnt) {''')
    name = 'include/ra2-ps-retain.h'
    if name in result or (source / name).exists():
        raise ValueError('ra2 PS retention already present')
    result[name] = (local / 'ra2-ps-retain.h').read_text()
    return result
