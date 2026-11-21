"""Prepare factored HOSTAPD key helpers for this SDK's embedded wifi_dev fields.

Not a full HOSTAPD port or an installed driver transformation.
"""
def compose(helpers):
    replacements=(
      ('pMbss->DefaultKeyId','pMbss->wdev.DefaultKeyId',20),
      ('pAd->ApCfg.MBSSID[pEntry->func_tb_idx].DefaultKeyId',
       'pAd->ApCfg.MBSSID[pEntry->func_tb_idx].wdev.DefaultKeyId',1),
      ('pAd->ApCfg.MBSSID[apidx].GroupKeyWepStatus',
       'pAd->ApCfg.MBSSID[apidx].wdev.GroupKeyWepStatus',4))
    for old,new,count in replacements:
        if helpers.count(old)!=count:raise ValueError('native key layout anchor changed: '+old)
        helpers=helpers.replace(old,new)
    return helpers
