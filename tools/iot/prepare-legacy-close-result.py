#!/usr/bin/env python3
"""Propagate legacy driver close result; requires coherent OS_ABL module rebuild."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:
 p.error('new separate output required')
pins={
 'common/rtmp_init_inf.c':'d26a84c77f53bc29cfc85e38b8893035c5c322ffce8822863c7f149be875d1f7',
 'include/rt_os_net.h':'f722d3c3694987483970cad8b402769e7c057fe1cc262e10e4a1890ba86c91ca',
 'os/linux/rt_main_dev.c':'3f12c64c8b84065b17250192b5baaa8edfdea9c22e01cc6cdaa4f644b2dec64e',
 'common/cmm_cfg.c':'ab9e85630cd337067b5538d76c5e8c0b8c7647a099bebeb1c7f1f71734cfdb44',
 'os/linux/pci_main_dev.c':'b4ed5ac669063dae5126c415cf23a638084e1bb22f776792e32923b75079da7a',
 'os/linux/rt_profile.c':'467d4a8d696fc9a9d47cd0a513e167e94c57be3f2f8fa47cd5c8836cd89e3421',
 'ap/ap_apcli_inf.c':'11254710fd0391b6053e3af002f0a032f04c54e97cefd4d0d659d0b87ce10a2d',
}
for name,digest in pins.items():
 if hashlib.sha256((src/name).read_bytes()).hexdigest()!=digest:p.error('unreviewed predecessor: '+name)
texts={name:(src/name).read_text() for name in pins}
def one(s,old,new):
 if s.count(old)!=1:p.error('unreviewed anchor: '+old)
 return s.replace(old,new,1)
s=texts['common/rtmp_init_inf.c'];start=s.index('VOID RTMPDrvClose(');end=s.index('\n}',start)+2
body=one(s[start:end],'VOID RTMPDrvClose(', 'INT RTMPDrvClose(')
body=one(body,'if (!APShutdown(pAd)) return;', 'if (!APShutdown(pAd)) return NDIS_STATUS_FAILURE;')
body=body[:-1]+'\treturn NDIS_STATUS_SUCCESS;\n}'
texts['common/rtmp_init_inf.c']=s[:start]+body+s[end:]
s=texts['include/rt_os_net.h']
s=one(s,'VOID (*RTMPDrvClose)(VOID *pAd, VOID *net_dev);','INT (*RTMPDrvClose)(VOID *pAd, VOID *net_dev);')
s=one(s,'VOID RTMPDrvClose(VOID *pAd, VOID *net_dev);','INT RTMPDrvClose(VOID *pAd, VOID *net_dev);')
start=s.index('__inline VOID VIRTUAL_IF_DOWN(');end=s.index('\n}',start)+2
body=one(s[start:end],'__inline VOID VIRTUAL_IF_DOWN(', '__inline INT VIRTUAL_IF_DOWN(')
call='RTMP_COM_IoctlHandle(pAd, NULL, CMD_RTPRIV_IOCTL_VIRTUAL_INF_DOWN,\n\t\t\t\t\t\t0, &InfConf, 0);'
body=one(body,call,'if ('+call[:-1]+' != NDIS_STATUS_SUCCESS) return -1;')
body=one(body,'return;', 'return 0;')
texts['include/rt_os_net.h']=s[:start]+body+s[end:]
texts['os/linux/rt_main_dev.c']=one(texts['os/linux/rt_main_dev.c'],
 'RTMPDrvClose(pAd, net_dev);', 'if (RTMPDrvClose(pAd, net_dev) != NDIS_STATUS_SUCCESS) return -EIO;')
texts['common/cmm_cfg.c']=one(texts['common/cmm_cfg.c'],
 'pInfConf->rt28xx_close(pAd->net_dev);',
 'if (pInfConf->rt28xx_close(pAd->net_dev) != 0) return NDIS_STATUS_FAILURE;')
texts['os/linux/pci_main_dev.c']=one(texts['os/linux/pci_main_dev.c'],
 'rt28xx_close((PNET_DEV)net_dev);', 'if (rt28xx_close((PNET_DEV)net_dev) != 0) return -EBUSY;')
for rel in ['os/linux/rt_profile.c','ap/ap_apcli_inf.c']:
 texts[rel]=one(texts[rel],'VIRTUAL_IF_DOWN(pAd);', 'if (VIRTUAL_IF_DOWN(pAd) != 0) return -EBUSY;')
shutil.copytree(src,out)
for name,text in texts.items():(out/name).write_text(text,encoding='utf-8',newline='\n')
out.with_name(out.name+'-legacy-close-result.json').write_text(json.dumps({
 'input_sha256':pins,'output_sha256':{name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in pins},
 'scope':'legacy close status and immediate consumers including Monitor/APCLI; lifetime unaccepted',
 'legacy_virtual_down_callers_checked':2,
 'os_abl_return_contract_changed':True,'coherent_target_module_rebuild_required':True,
 'target_compiled':False,'runtime_verified':False,'lifecycle_accepted':False,
},indent=2)+'\n',encoding='utf-8')
print('Staged legacy close status, OS_ABL declaration, PCI and virtual-down refusal')
