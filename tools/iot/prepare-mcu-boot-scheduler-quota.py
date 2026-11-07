#!/usr/bin/env python3
"""Stage checked SDK scheduler copy; no MCUSysInit binding."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
p.add_argument('--install-isolated',action='store_true',required=True)
a=p.parse_args();src=a.source.resolve();mp=Path(str(src)+'.manifest.json')
raw=mp.read_bytes();m=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if (m.get('production_installed') is not False or m.get('target_compiled') is not False
 or 'mcu_boot_scheduler_owner' not in m or 'mcu_boot_scheduler_quota' in m or actual!=m['merged_driver_sha256']):
 p.error('Expected unchanged isolated scheduler-owner candidate')
name='hw_ctrl/cmm_asic_mt.c';text=(src/name).read_text()
start=text.index('INT32 AsicDMASchedulerInit(RTMP_ADAPTER *pAd, INT mode)')
end=text.index('\n}\n',start)+3;original=text[start:end]
body=original.replace('AsicDMASchedulerInit(', 'wr_iot_boot_sdk_scheduler_checked(',1)
anchor='\tINT dma_mode = mode;'
if body.count(anchor)!=1:p.error('Changed SDK mode declaration')
body=body.replace(anchor,anchor+'''
 UINT32 quota_beacon=0,quota_data,quota_ap=0;
 /* Private bootstrap supports only PCI AP LMAC. Reject before any MMIO. */
#if !defined(RTMP_PCI_SUPPORT) || !defined(CONFIG_AP_SUPPORT)
 return FALSE;
#else
 IF_DEV_CONFIG_OPMODE_ON_AP(pAd) { quota_ap=1; }
 if(!quota_ap || mode!=DMA_SCH_LMAC)return FALSE;
#endif
''')
anchor='\tRTMP_IO_READ32(pAd, 0x80120, &mac_val);'
if body.count(anchor)!=1:p.error('Changed SDK quota-read anchor')
body=body.replace(anchor,anchor+'''
 if(mac_val==~(UINT32)0 || !((mac_val>>16)&0xfffU)) {
  RTMP_IO_WRITE32(pAd, MCU_PCIE_REMAP_2, mac_restore_val);
  return FALSE;
 }
''')
anchor='\t/* Setting PSE page free priority'
if body.count(anchor)!=1:p.error('Changed SDK first scheduler write anchor')
body=body.replace(anchor,''' /* Validate group arithmetic before the first scheduler register write.
  * Remap acquisition still needs external producer serialization. */
 if(dma_mode!=DMA_SCH_LMAC)return FALSE;
 quota_data=(pAd->CommonCfg.BACapability.field.AmsduEnable==TRUE ?
             MAX_AMSDU_DATA_SIZE:MAX_DATA_SIZE)/page_size;
#ifdef CONFIG_AP_SUPPORT
 quota_beacon=quota_data;
 if(pAd->ApCfg.BssidNum>1)
  quota_beacon+=(MAX_BEACON_SIZE/page_size)*(pAd->ApCfg.BssidNum-1);
#endif
 if(!(MTK_REV_GTE(pAd,MT7603,MT7603E1)&&MTK_REV_LT(pAd,MT7603,MT7603E2)) &&
    (quota_beacon>page_cnt || MAX_MCUCMD_SIZE/page_size>=page_cnt-quota_beacon))
  return FALSE;

'''+anchor)
anchor='\t\t\t/* Group 0 + 1+ 2 = PSE P0  */'
if body.count(anchor)!=1:p.error('Changed SDK group subtraction anchor')
body=body.replace(anchor,'''            if(bcn_restore_val>page_cnt ||
               mcu_restore_val>=page_cnt-bcn_restore_val)return FALSE;
'''+anchor)
changes={name:text[:end]+'\n'+body+text[end:]}
name='include/rtmp_chip.h';text=(src/name).read_text()
anchor='INT32 AsicDMASchedulerInit(struct _RTMP_ADAPTER *pAd, INT mode);'
if text.count(anchor)!=1:p.error('Changed SDK prototype anchor')
changes[name]=text.replace(anchor,anchor+'\nINT32 wr_iot_boot_sdk_scheduler_checked(struct _RTMP_ADAPTER *pAd, INT mode);')
name='include/wr-iot-mcu-boot-scheduler.inc';text=(src/name).read_text()
anchor='AsicDMASchedulerInit(ad,DMA_SCH_LMAC)'
if text.count(anchor)!=1:p.error('Changed checker SDK call')
changes[name]=text.replace(anchor,'wr_iot_boot_sdk_scheduler_checked(ad,DMA_SCH_LMAC)')
for name,text in changes.items():(src/name).write_text(text)
hashes={name:hashlib.sha256((src/name).read_bytes()).hexdigest() for name in changes}
m['merged_driver_sha256'].update(hashes);m['candidate_driver_sha256'].update(hashes)
m['mcu_boot_scheduler_quota']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),
 'sdk_body_sha256':hashlib.sha256(original.encode()).hexdigest(),'output_sha256':hashes,
 'remap_serialized':False,'bound':False,'target_compiled':False,'runtime_verified':False}
mp.write_text(json.dumps(m,indent=2)+'\n')
