#!/usr/bin/env python3
"""Emit an opt-in diagnostic patch against pinned MT7603 vendor source; no install."""
import argparse,difflib,hashlib
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('driver',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
changes={}
header='''/* Diagnostic only. Build with -DWR_IOT_PSM_DIAG; off by default.
 * Per-translation-unit event counters count instrumented hits even when log
 * lines are suppressed. Not hardware totals, per-BSS totals or retry rate.
 * Caller supplies only stable scalar values, never borrowed peer pointers. */
#ifndef WR_IOT_PSM_DIAG_H
#define WR_IOT_PSM_DIAG_H
#ifdef WR_IOT_PSM_DIAG
#include <linux/atomic.h>
#include <linux/ratelimit.h>
static inline void wr_iot_ps_diag(unsigned int event,unsigned int bss,
 unsigned int peer,unsigned int x,unsigned int y){
 static atomic_t hits[5]={ATOMIC_INIT(0),ATOMIC_INIT(0),ATOMIC_INIT(0),ATOMIC_INIT(0),ATOMIC_INIT(0)};
 static DEFINE_RATELIMIT_STATE(limit,5*HZ,8);
 unsigned int count;
 if(event>=5)return;
 count=(unsigned int)atomic_inc_return(&hits[event]);
 if(__ratelimit(&limit))
  printk(KERN_INFO "wr_ps event=%u bss=%u peer=%u x=%u y=%u hits=%u site=%s\\n",
   event,bss,peer,x,y,count,__FILE__);
}
#else
#define wr_iot_ps_diag(event,bss,peer,x,y) do {} while(0)
#endif
#endif
'''
changes['include/wr-iot-psm-diag.h']=('',header)
def edit(name,old,new):
 original=(a.driver/name).read_text();s=changes.get(name,(original,original))[1]
 if s.count(old)!=1:raise SystemExit('Diagnostic anchor changed: '+name+' '+old[:65])
 s=s.replace(old,new,1)
 if name not in changes:
  anchor='#include\t"rt_config.h"' if name=='tx_rx/txs.c' else '#include "rt_config.h"'
  if s.count(anchor)!=1:raise SystemExit('Include anchor changed '+name)
  s=s.replace(anchor,anchor+'\n#include "wr-iot-psm-diag.h"',1)
 changes[name]=(original,s)
edit('common/mt_ps.c','\told_psmode = pEntry->PsMode;', '''\told_psmode = pEntry->PsMode;
 if(old_psmode!=Psm)wr_iot_ps_diag(0,pEntry->func_tb_idx,wcid,old_psmode,Psm);''')
edit('ap/ap.c','\t\t\t\t\trtmp_tx_swq_exit(pAd, pEntry->wcid);','''     wr_iot_ps_diag(1,pEntry->func_tb_idx,pEntry->wcid,tr_entry->PsQIdleCount,tr_entry->enqCount);
\t\t\t\t\trtmp_tx_swq_exit(pAd, pEntry->wcid);''')
edit('ap/ap.c','\t\t\tbDisconnectSta = TRUE;\n\t\t\tDBGPRINT(RT_DEBUG_WARN, ("ageout', '''   wr_iot_ps_diag(2,pEntry->func_tb_idx,pEntry->wcid,pEntry->NoDataIdleCount,pEntry->StaIdleTimeout);
\t\t\tbDisconnectSta = TRUE;
\t\t\tDBGPRINT(RT_DEBUG_WARN, ("ageout''')
edit('ap/ap_connect.c','\t*(ptr + 3) = pAd->ApCfg.DtimPeriod;', '''\t*(ptr + 3) = pAd->ApCfg.DtimPeriod;
 wr_iot_ps_diag(3,apidx,0,pAd->ApCfg.DtimCount,pAd->ApCfg.DtimPeriod);''')
# RX reports already delivered to host only; do not enable extra TX status requests.
sig='INT32 ParseTxSPacket(RTMP_ADAPTER *pAd, UINT32 Pid, UINT8 Format, CHAR *Data)\n{'
edit('tx_rx/txs.c',sig,sig+'''
#ifdef WR_IOT_PSM_DIAG
 TXS_STRUC *diag=(TXS_STRUC *)Data;
 /* Format0 only; WCID is a report identity, never dereferenced for attribution.
  * x=ME/RE/LE/BE bits, y=raw MPDU transmit count, NOT retry count. */
 if(Format==TXS_FORMAT0 && Data)
  wr_iot_ps_diag(4,~0U,diag->txs_d3.wlan_idx,
   diag->txs_d0.ME|(diag->txs_d0.RE<<1)|(diag->txs_d0.LE<<2)|(diag->txs_d0.BE<<3),
   diag->txs_d4.mpdu_tx_cnt);
#endif''')
# Move instrumentation after local declarations for kernel gnu89 compatibility.
orig,txt=changes['tx_rx/txs.c'];start=txt.index('\n#ifdef WR_IOT_PSM_DIAG',txt.index(sig));end=txt.index('\n#endif',start)+len('\n#endif');block=txt[start:end];txt=txt[:start]+txt[end:];anchor='\tif (TxSCtl->TxSValid == FALSE)';assert txt.count(anchor)==1;txt=txt.replace(anchor,block+'\n'+anchor,1);changes['tx_rx/txs.c']=(orig,txt)
patch=''
for name,(old,new) in changes.items():
 patch+=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+name if old else '/dev/null',tofile='b/'+name))
a.output.write_text(patch)
print('Generated',a.output,'files',len(changes),'sha256',hashlib.sha256(patch.encode()).hexdigest())
