#!/usr/bin/env python3
"""Install bounded allocation-free checked ACK dispatch in an isolated candidate."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--install-isolated',action='store_true',required=True);a=p.parse_args()
src=a.source.resolve();mp=Path(str(src)+'.manifest.json');raw=mp.read_bytes();manifest=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if (manifest.get('production_installed') is not False or manifest.get('target_compiled') is not False or
    'mcu_boot_result' not in manifest or 'mcu_rx_direct' in manifest or actual!=manifest['merged_driver_sha256']):
 p.error('Expected unchanged isolated boot-result candidate')
mt=(src/'mcu/andes_mt.c').read_text();data=(src/'common/cmm_data.c').read_text();header=(src/'include/mcu/andes_mt.h').read_text()
start=mt.index('                if (msg->wr_iot_checked) {');end=mt.index('\n\t\t\t#if defined(RTMP_USB_SUPPORT)',start)
branch=mt[start:end]
if mt.count(branch)!=1:raise SystemExit('Changed checked ACK branch')
branch=branch.replace('GET_OS_PKT_LEN(net_pkt)','length').replace('GET_OS_PKT_DATAPTR(net_pkt)','data')
helper='''/* Caller owns a DMA-valid packet and joined RX lifetime. No constructor,
 * allocation, generic callback, sequence reset or normal sender rearm here. */
BOOLEAN wr_iot_mcu_checked_rx_packet(RTMP_ADAPTER *ad,UCHAR *data,UINT32 length)
{
 EVENT_RXD storage,*event_rxd=&storage;
 struct MCU_CTRL *ctl;
 struct cmd_msg *msg,*msg_tmp;
 unsigned long flags=0;
 BOOLEAN handled=FALSE;
 if(!ad||!data||length<sizeof(storage))return TRUE;
 ctl=&ad->MCUCtrl;
 if(!OS_TEST_BIT(MCU_INIT,&ctl->flags))return TRUE;
 NdisMoveMemory(&storage,data,sizeof(storage));
 /* PCI parser already converted dword0 on big-endian hosts. */
 storage.fw_rxd_1.word=le2cpu32(storage.fw_rxd_1.word);
 storage.fw_rxd_2.word=le2cpu32(storage.fw_rxd_2.word);
 if(storage.fw_rxd_0.field.length!=length)return TRUE;
 if(!storage.fw_rxd_1.field.seq_num)return FALSE;
 RTMP_SPIN_LOCK_IRQSAVE(&ctl->ackq_lock,&flags);
 DlListForEachSafe(msg,msg_tmp,&ctl->ackq,struct cmd_msg,list) {
  if(msg->seq!=storage.fw_rxd_1.field.seq_num||!msg->wr_iot_checked)continue;
  handled=TRUE;
'''+branch+'''
 }
 RTMP_SPIN_UNLOCK_IRQRESTORE(&ctl->ackq_lock,&flags);
 return handled;
}
'''
anchor='VOID AndesMTRxEventHandler(RTMP_ADAPTER *pAd, UCHAR *data)'
if mt.count(anchor)!=1:raise SystemExit('Changed MCU RX entry')
mt=mt.replace(anchor,'#if defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)\n#include "wr-iot-mcu-rx-direct.inc"\n#endif\n\n'+anchor)
anchor='VOID AndesMTRxEventHandler(struct _RTMP_ADAPTER *pAd, UCHAR *data);'
if header.count(anchor)!=1:raise SystemExit('Changed MCU RX declaration')
header=header.replace(anchor,anchor+'\n#if defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)\nBOOLEAN wr_iot_mcu_checked_rx_packet(struct _RTMP_ADAPTER *ad,UCHAR *data,UINT32 length);\n#endif')
anchor='''            if (ad->chipOps.rx_event_handler != NULL)
                ad->chipOps.rx_event_handler(ad, GET_OS_PKT_DATAPTR(rx_packet));'''
if data.count(anchor)!=1 or 'if (rx_blk->PDMALen < sizeof(EVENT_RXD)) break;' not in data:raise SystemExit('Expected bounded PCI RX event entry')
data=data.replace(anchor,'''#if defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
            if (!wr_iot_mcu_checked_rx_packet(ad, GET_OS_PKT_DATAPTR(rx_packet),rx_blk->PDMALen)) {
#endif
'''+anchor+'''
#if defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
            }
#endif''')
changes={'mcu/andes_mt.c':mt,'common/cmm_data.c':data,'include/mcu/andes_mt.h':header,'include/wr-iot-mcu-rx-direct.inc':helper}
for name,text in changes.items():(src/name).write_text(text)
hashes={n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in changes}
manifest['merged_driver_sha256'].update(hashes);manifest['candidate_driver_sha256'].update(hashes)
manifest['mcu_rx_direct']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,'scope':'bounded checked ACK dispatch without allocation; ordinary RX fallback unchanged','target_compiled':False,'runtime_verified':False,'firmware_epoch_verified':False}
mp.write_text(json.dumps(manifest,indent=2)+'\n')
