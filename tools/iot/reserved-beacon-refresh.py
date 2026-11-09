"""Scope the generated claimed-UP refresh; leave periodic/legacy paths intact."""
START='\t\t\tif (pInfConf->owner_generation ||'
END='\t\t\t/* Arithmetic guard only;'
CALL='\t\t\t\t\tAPUpdateAllBeaconFrame(pAd);'
GUARDED='''\t\t\t\t\t/* Reserved ra2 uses the normal periodic DTIM tick. */
\t\t\t\t\tif (!(IS_MT7603(pAd) && pAd->chipCap.hif_type == HIF_MT &&
\t\t\t\t\t      pAd->ApCfg.BssidNum == 3 && claim.operation == WR_RADIO_BSS_OPEN &&
\t\t\t\t\t      claim.device == pAd->ApCfg.MBSSID[2].wdev.if_dev))
\t\t\t\t\t\tAPUpdateAllBeaconFrame(pAd);'''
def compose(text):
 if text.count(START)!=1:raise ValueError('Claimed-UP boundary changed')
 start=text.index(START);end=text.index(END,start)
 block=text[start:end]
 if block.count(CALL)!=1 or 'Reserved ra2 uses' in block:
  raise ValueError('Claimed-UP refresh changed or already scoped')
 return text[:start]+block.replace(CALL,GUARDED,1)+text[end:]
