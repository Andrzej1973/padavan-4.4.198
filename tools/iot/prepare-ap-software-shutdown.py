#!/usr/bin/env python3
"""Stage separate AP cleanup entry before radio-off; unbound, not production accepted."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:
 p.error('new separate output required')
pins={'ap/ap.c':'d08fdb07a2c42effcde899e4fa0c01c654709c78b3c05f9e06792644b73b7d76','include/ap.h':'eaaae8eb8854dede4be05da3a8e3a49cf868eadd9edaa354614d0a554de509b1'}
for n,h in pins.items():
 if hashlib.sha256((src/n).read_bytes()).hexdigest()!=h:p.error('unreviewed source: '+n)
s=(src/'ap/ap.c').read_text()
def span(text,sig):
 start=text.index(sig);end=text.index('\n}',start)+2
 return start,end,text[start:end]
def once(text,old,new):
 if text.count(old)!=1:p.error('changed anchor: '+old)
 return text.replace(old,new,1)
# Shared bodies preserve every cleanup operation; only hardware actions differ.
i,j,body=span(s,'BOOLEAN APStop(RTMP_ADAPTER *pAd)')
body=once(body,'BOOLEAN APStop(RTMP_ADAPTER *pAd)','static BOOLEAN wr_iot_ap_stop_body(RTMP_ADAPTER *pAd, BOOLEAN hardware)')
body=once(body,'\tRTMP_ASIC_INTERRUPT_DISABLE(pAd);','\tif (hardware) RTMP_ASIC_INTERRUPT_DISABLE(pAd);')
body=once(body, '\tDBGPRINT(RT_DEBUG_TRACE, (\"!!! APStop !!!\\n\"));', '(void)hardware;\n\tDBGPRINT(RT_DEBUG_TRACE, (\"!!! APStop !!!\\n\"));')
wrapper='\nBOOLEAN APStop(RTMP_ADAPTER *pAd)\n{\n return wr_iot_ap_stop_body(pAd, TRUE);\n}\n'
s=s[:i]+body+wrapper+s[j:]
i,j,body=span(s,'BOOLEAN APShutdown(RTMP_ADAPTER *pAd)')
body=once(body,'BOOLEAN APShutdown(RTMP_ADAPTER *pAd)','static BOOLEAN wr_iot_ap_shutdown_body(RTMP_ADAPTER *pAd, BOOLEAN hardware)')
body=once(body,'\t\tMlmeRadioOff(pAd);','\t\tif (hardware) MlmeRadioOff(pAd);')
body=once(body,'APStop(pAd)','wr_iot_ap_stop_body(pAd, hardware)')
wrappers='''
BOOLEAN APShutdown(RTMP_ADAPTER *pAd)
{
 return wr_iot_ap_shutdown_body(pAd, TRUE);
}
/* Caller must own checked shutdown and keep MCU RX/IRQ live until OFF ACK.
 * This entry still performs destructive AP software cleanup; not a preflight.
 * Unbound candidate: no radio/IRQ/DMA completion or retry proof is implied. */
BOOLEAN wr_iot_ap_shutdown_before_radio_off(RTMP_ADAPTER *pAd)
{
 return wr_iot_ap_shutdown_body(pAd, FALSE);
}
'''
s=s[:i]+body+wrappers+s[j:]
# Declaration must follow vendor includes, so place immediately before shutdown.
pos=s.index('static BOOLEAN wr_iot_ap_shutdown_body(')
s=s[:pos]+'static BOOLEAN wr_iot_ap_stop_body(RTMP_ADAPTER *pAd, BOOLEAN hardware);\n'+s[pos:]
h=(src/'include/ap.h').read_text();h=once(h,'BOOLEAN APShutdown(RTMP_ADAPTER *pAd);','BOOLEAN APShutdown(RTMP_ADAPTER *pAd);\nBOOLEAN wr_iot_ap_shutdown_before_radio_off(RTMP_ADAPTER *pAd);')
shutil.copytree(src,out)
(out/'ap/ap.c').write_text(s);(out/'include/ap.h').write_text(h)
r={'input_sha256':pins,'output_sha256':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in pins},'scope':'unbound AP cleanup entry before radio-off; legacy wrappers retain hardware actions','production_installed':False,'target_compiled':False,'runtime_verified':False}
out.with_name(out.name+'.ap-software.json').write_text(json.dumps(r,indent=2)+'\n')
print('Staged unbound AP cleanup before radio-off; checked close order and retry binding remain open')
