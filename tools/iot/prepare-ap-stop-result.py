#!/usr/bin/env python3
"""Propagate AP stop refusal through reviewed direct callers, not outer release."""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:
 p.error('new separate output required')
pins={
 'ap/ap.c':'6d8392cac8b97023107c58d332fe41a232e9b5c00278608c8e1bf10e3d5d00de',
 'include/ap.h':'85fc113b0ec9ed0e71d925917b64e4788488a5babd38bc752f5fa3b09e05e3d2',
 'ap/ap_cfg.c':'14b110a764b9eef9a8165b1648e03fbf7eb9090025779f5c532be9decfc49d2d',
 'ap/ap_mix_mode.c':'7dfb726509001f0b76706ec31f64fd0f88676c0bb530248423da20804f9e79ba',
 'ate/mt_mac/mt_ate.c':'6be34b12ccb1f2a7f3526a94006a01252f6114e2eb1c84b6614bf36c4c611904',
 'common/cmm_info.c':'9ed0cc16ff7794d26054e160b2b460e0e6d3de39e3f505e04838f2b53f478cd6',
 'common/cmm_radar.c':'7b10866fcc7eb5bd8967437973a66f4a529fa7e3c665a5b44a0b45792830db16',
 'common/cmm_usb_io.c':'eb7daeca40a06e057b118dda3053ebecb26c90d0849f0c30d3b3e113acfd0a69',
 'common/mtusb_io.c':'b64c40f3076ce4e4212b7346d41366e2bfd740be38530a343de307b194d6d788',
 'common/rtmp_init.c':'ba039e2c12b551d70727063bc1c3f94898ecce9b846e828e486dd3fbb2f7b589',
 'common/scan.c':'5d08880ccbc24ead94d22f1f1961bb339ccf057c95fc7e18fd183ad49f695810',
 'common/wsc.c':'4d209fa6d6dc0fa5d2fa94ad0f32366ac66a9e6fae382cabea65ab5cbb4eee91',
 'easy_setup/mt7603_chip_ops.c':'fea58ded16d0fb46e8b312bec334cf6e0f6a2d9dc24f9693095b5dcd3ac58df8',
 'easy_setup/mt7603_chip_ops_api.c':'9f518bd2a0572784936f97f84baafb8b5648c84156527be18b42e358799ffadc',
 'hw_ctrl/cmm_asic_mt.c':'c1dbe60dacf9f2a1feaec9bc77c15c9d3d4323239ef78e247c2e37944d044ad8',
 'os/linux/rt_rbus_pci_drv.c':'a9a178f908874cf942246dc441ae2f75b5813299033b19d676d66fdc96703ee0',
}
for name,digest in pins.items():
 if hashlib.sha256((src/name).read_bytes()).hexdigest()!=digest:p.error('unreviewed predecessor: '+name)
texts={name:(src/name).read_text() for name in pins}
def one(s,old,new):
 if s.count(old)!=1:p.error('unreviewed anchor: '+old)
 return s.replace(old,new,1)
s=texts['ap/ap.c']
for name in ['APStop','APStopBssOnly']:
 sig='VOID '+name+'(';start=s.index(sig);end=s.index('\n}',start)+2
 body=s[start:end];body=one(body,sig,'BOOLEAN '+name+'(')
 body=body.replace('return;','return FALSE;')
 body=body[:-1]+'\treturn TRUE;\n}'
 s=s[:start]+body+s[end:]
 texts['include/ap.h']=one(texts['include/ap.h'],sig,'BOOLEAN '+name+'(')
texts['ap/ap.c']=one(s,'APStop(pAd);','if (!APStop(pAd)) return;')
# UFD ioctl must preserve the allocated filename cleanup; no early return/break.
s=texts['ap/ap_cfg.c']
pattern=r'APStop\(pAd\);\s*APStartUp\(pAd\);'
matches=list(re.finditer(pattern,s))
if len(matches)!=6:p.error('unreviewed ioctl/SSID stop-start count')
for index,m in reversed(list(enumerate(matches))):
 if index==0:new='if (APStop(pAd)) APStartUp(pAd);\n\t\t\t\t\t\t\t\telse Status = -EBUSY;'
 elif index<3:new='if (!APStop(pAd)) { Status = -EBUSY; break; }\n\t\t\tAPStartUp(pAd);'
 else:new='if (!APStop(pAd)) return FALSE;\n\t\t\t\tAPStartUp(pAd);'
 s=s[:m.start()]+new+s[m.end():]
texts['ap/ap_cfg.c']=s
# Reviewed local failure semantics: retain state and leave before later actions.
rules={
 'ap/ap_mix_mode.c':(1,'return FALSE;'),
 'ate/mt_mac/mt_ate.c':(1,'return -1;'),
 'common/cmm_info.c':(4,'return FALSE;'),
 'common/cmm_radar.c':(1,'return;'),
 'common/cmm_usb_io.c':(1,'return NDIS_STATUS_FAILURE;'),
 'common/mtusb_io.c':(1,'return NDIS_STATUS_FAILURE;'),
 'common/rtmp_init.c':(1,'break;'), # switch exit preserves command-buffer free below
 'common/scan.c':(1,'return FALSE;'),
 'common/wsc.c':(2,'return;'),
 'easy_setup/mt7603_chip_ops.c':(2,'return FALSE;'),
 'easy_setup/mt7603_chip_ops_api.c':(2,'return FALSE;'),
 'hw_ctrl/cmm_asic_mt.c':(1,'return;'),
 'os/linux/rt_rbus_pci_drv.c':(1,'return;'),
}
for rel,(count,action) in rules.items():
 if texts[rel].count('APStop(pAd);')!=count:p.error('unreviewed caller count: '+rel)
 texts[rel]=texts[rel].replace('APStop(pAd);','if (!APStop(pAd)) '+action)
# Every executable APStop call is now explicitly checked; prototypes excluded.
coverage={}
for rel,s in texts.items():
 count=len(re.findall(r'\bif \(!?APStop\(pAd\)\)',s))
 if count:coverage[rel]=count
if sum(coverage.values())!=26:p.error('APStop direct coverage mismatch')
shutil.copytree(src,out)
for name,text in texts.items():(out/name).write_text(text,encoding='utf-8',newline='\n')
out.with_name(out.name+'-ap-stop-result.json').write_text(json.dumps({
 'input_sha256':pins,
 'output_sha256':{name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in pins},
 'checked_apstop_calls':coverage,'scope':'direct APStop refusal only; outer VOID parents and prior side effects remain',
 'target_compiled':False,'runtime_verified':False,'lifecycle_accepted':False,
},indent=2)+'\n',encoding='utf-8')
print('Staged BOOLEAN APStop/APStopBssOnly and 26 checked direct callers')
