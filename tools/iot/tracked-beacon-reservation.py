"""Require the current tracked ra2 beacon token before lower submission.

This is not the future non-owning PID mode. A zero generation is a failed
tracked allocation, not authorization to submit without TxS-dependent pacing.
"""
SIGNATURE = 'INT32 RT28xx_UpdateBeaconToAsic('
GUARD = '''
\t/* Tracked ra2 requires a reservation; no non-owning mode is bound. */
\tif (IS_MT7603(pAd) && pAd->chipCap.hif_type == HIF_MT &&
\t    pAd->ApCfg.BssidNum == 3 && apidx == 2 && !reservation.generation)
\t\treturn -1;
'''


LOCKED_GUARD = '''
		/* Revalidate the current BSS layout at the submission lock. */
		if (IS_MT7603(pAd) && pAd->chipCap.hif_type == HIF_MT &&
		    pAd->ApCfg.BssidNum == 3 && apidx == 2 && !reservation.generation) {
			RTMP_SEM_UNLOCK(&pAd->BcnRingLock);
			goto unsubmitted;
		}
'''


def selected(source):
    start = source.index(SIGNATURE)
    end = source.index('\n}', start) + 2
    return start, end, source[start:end]


def compose(source):
    if 'Tracked ra2 requires a reservation' in source:
        raise ValueError('Tracked reservation guard already installed')
    start, end, function = selected(source)
    # The other implementation is the legacy RLT branch. Identify MT by its
    # packet lookup and checked HAL, rather than patching every same-name ABI.
    if function.count('HAL_KickOutMgmtTx(') != 2 or 'goto unsubmitted;' not in function:
        raise ValueError('Expected checked MT PCI beacon submission')
    anchor = '\tif (!pAd) return -1;'
    if function.count(anchor) != 1:
        raise ValueError('Tracked submission null-adapter anchor changed')
    function = function.replace(anchor, anchor + GUARD, 1)
    lock = '\t\tRTMP_SEM_LOCK(&pAd->BcnRingLock);'
    if function.count(lock) != 1:
        raise ValueError('MT submit ring lock changed')
    function = function.replace(lock, lock + LOCKED_GUARD, 1)
    if function.index(GUARD) > function.index('bcn_buf = &pAd->ApCfg.MBSSID'):
        raise ValueError('Guard must precede packet lookup/mutation')
    return source[:start] + function + source[end:]
