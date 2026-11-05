#!/usr/bin/env python3
"""Prepare transactional RX payload replacement after ROM quiesce; hardware rearm remains unfinished."""
import argparse
import hashlib
import json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--install-isolated',action='store_true',required=True);a=p.parse_args()
src=a.source.resolve();mp=Path(str(src)+'.manifest.json');raw=mp.read_bytes();manifest=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if (manifest.get('production_installed') is not False or manifest.get('target_compiled') is not False or
    'mcu_boot_pse_drain' not in manifest or 'mcu_boot_rx_refresh' in manifest or actual!=manifest['merged_driver_sha256']):
 p.error('Expected unchanged isolated composed PSE drain candidate')
util=(src/'os/linux/rt_rbus_pci_util.c').read_text();start=util.index('PNDIS_PACKET RTMP_AllocateRxPacketBuffer(');end=util.index('\n}',start)+2
if hashlib.sha256(util[start:end].encode()).hexdigest()!='d6f8ad8822aff2687627e8492041fa9440421e44cf4ef3ea7ae0fb80b4c4a83e':raise ValueError('Unreviewed RX packet allocator')
sdk=(src/'include/mac/mac_mt/mt_mac_pci.h').read_text()
start=sdk.rfind('#ifdef RT_BIG_ENDIAN',0,sdk.index('typedef\tstruct GNU_PACKED _RXD_STRUC'))
end=sdk.index('#endif /* RT_BIG_ENDIAN */',start)+len('#endif /* RT_BIG_ENDIAN */')
if hashlib.sha256(sdk[start:end].encode()).hexdigest()!='e5b7274534b0cec95db03517aa5ea04777079541e81f00a7676565090ba1ce2a':raise ValueError('Unreviewed MT RX descriptor layout')
source=(src/'common/cmm_data_pci.c').read_text();header=(src/'include/rtmp.h').read_text()
source+='\n#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)\n#include "wr-iot-mcu-boot-rx-refresh.inc"\n#endif\n'
anchor='INT RtmpNetTaskExit(RTMP_ADAPTER *pAd);';assert header.count(anchor)==1
header=header.replace(anchor,anchor+'\n#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)\nINT wr_iot_mcu_boot_rx_refresh(RTMP_ADAPTER *ad);\n#endif')
changes={'common/cmm_data_pci.c':source,'include/rtmp.h':header,'include/wr-iot-mcu-boot-rx-refresh.inc':Path(__file__).with_name('mcu-boot-rx-refresh.inc').read_text()}
for name,value in changes.items():(src/name).write_text(value)
hashes={n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in changes}
manifest['merged_driver_sha256'].update(hashes);manifest['candidate_driver_sha256'].update(hashes)
manifest['mcu_boot_rx_refresh']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,'reviewed_allocator_sha256':actual['os/linux/rt_rbus_pci_util.c'],'reviewed_descriptor_header_sha256':actual['include/mac/mac_mt/mt_mac_pci.h'],'scope':'transactional replacement of both RX payload inventories; no index reset, hardware rearm or epoch commit','target_compiled':False,'runtime_verified':False,'firmware_epoch_verified':False,'loader_bound':False}
mp.write_text(json.dumps(manifest,indent=2)+'\n')
