"""Compose persistent idle-probe storage and both existing retirement fences.

Pure source transformer; not installed automatically. Caller must compose the
endpoint and compile the complete isolated tree before exposing the query.
"""
def once(text,old,new):
    if text.count(old)!=1:
        raise ValueError('Initial-idle lifetime anchor changed: '+old)
    return text.replace(old,new,1)

def storage(header,init):
    if "wr_iot_idle_probe" in header or "wr_iot_idle_probe" in init:
        raise ValueError("Initial-idle storage already installed")
    header=once(header,'#include "mbss-closed-probe.h"',
                '#include "mbss-closed-probe.h"\n#include "precreated-idle-probe.h"')
    header=once(header,' struct wr_iot_mbss_closed_probe wr_iot_closed_probe;',
                ' struct wr_iot_mbss_closed_probe wr_iot_closed_probe;\n struct wr_iot_precreated_idle_probe wr_iot_idle_probe;')
    anchor='NdisZeroMemory(&pAd->wr_iot_closed_probe,sizeof(pAd->wr_iot_closed_probe));'
    init=once(init,anchor,anchor+'\n        NdisZeroMemory(&pAd->wr_iot_idle_probe,sizeof(pAd->wr_iot_idle_probe));')
    return header,init

def retirement(work,join):
    work=once(work,' if(ad && wr_iot_driver_close_blocks_adapter_retirement(&ad->wr_iot_close_owner))return FALSE;',
              ' if(ad && (ad->wr_iot_idle_probe.active ||\n     wr_iot_driver_close_blocks_adapter_retirement(&ad->wr_iot_close_owner)))return FALSE;')
    join=once(join,' if(wr_iot_driver_close_blocks_adapter_retirement(&ad->wr_iot_close_owner))ready=0;',
              ' if(ad->wr_iot_idle_probe.active ||\n    wr_iot_driver_close_blocks_adapter_retirement(&ad->wr_iot_close_owner))ready=0;')
    return work,join
