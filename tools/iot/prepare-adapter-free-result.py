#!/usr/bin/env python3
"""Carry adapter-free refusal through native/OS_ABL and all direct callers.

This does not add a retirement claim or authorize adapter release.
"""
import argparse,hashlib,shutil,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
pins={'os/linux/rt_profile.c':'29e1655295d45043beff177ee61e698e70570c73a5ed0e8d8e19771ff40dde86',
 'include/rt_os_net.h':'2ab319d904d868079e1a847b7ca0f7ee1f4451670317a147e94f91063c781594',
 'common/rtmp_init.c':'b097b94e00224cc02f69f24ea58d96d7dbc2dc133b5368577a0920ca3c50ae9a',
 'os/linux/pci_main_dev.c':'e9215919b1e7cd6c8b2b137a8c958f69ad584e6c621d4d304f5eb044c83229e3',
 'os/linux/sdio_main_dev.c':'8d30142f99b9f567cd4ec48f0f61c3116f977070589f9fe49baa10d781eb4009'}
texts={}
for name,digest in pins.items():
 if hashlib.sha256((src/name).read_bytes()).hexdigest()!=digest:p.error('unreviewed predecessor: '+name)
 texts[name]=(src/name).read_text()
def one(name,old,new):
 if texts[name].count(old)!=1:p.error('changed anchor: '+name+': '+old)
 texts[name]=texts[name].replace(old,new,1)
one('include/rt_os_net.h','VOID (*RTMPFreeAdapter)(VOID *pAd);','BOOLEAN (*RTMPFreeAdapter)(VOID *pAd);')
one('include/rt_os_net.h','VOID RTMPFreeAdapter(VOID *pAd);','BOOLEAN RTMPFreeAdapter(VOID *pAd);')
name='os/linux/rt_profile.c';s=texts[name];start=s.index('VOID RTMPFreeAdapter(');end=s.index('\n}',start)+2
body=s[start:end].replace('VOID RTMPFreeAdapter(','BOOLEAN RTMPFreeAdapter(',1)
if body.count('return;')!=2:p.error('changed adapter-free refusal branches')
body=body.replace('return;','return FALSE;')
body=body[:-2]+'\n return TRUE;\n}'
texts[name]=s[:start]+body+s[end:]
one('common/rtmp_init.c','\tRTMPFreeAdapter(pAd);','\tif (!RTMPFreeAdapter(pAd)) return FALSE;')
one('os/linux/pci_main_dev.c','\tRTMPFreeAdapter(pAd);','\tif (!RTMPFreeAdapter(pAd)) return -EBUSY;')
one('os/linux/pci_main_dev.c','\t\tRtmpRaDevCtrlExit(pAd);','\t\tif (!RtmpRaDevCtrlExit(pAd)) return;')
one('os/linux/sdio_main_dev.c','\tRTMPFreeAdapter(pAd);','\tif (!RTMPFreeAdapter(pAd)) return;')
one('os/linux/sdio_main_dev.c','\t\tRtmpRaDevCtrlExit(pAd);','\t\tif (!RtmpRaDevCtrlExit(pAd)) return;')
shutil.copytree(src,out)
for name,text in texts.items():(out/name).write_text(text,encoding='utf-8',newline='\n')
out.with_name(out.name+'-manifest.json').write_text(json.dumps({'input_sha256':pins,
 'scope':'fallible free ABI and caller propagation only',
 'retirement_claim_bound':False,'controller_pre_destructor_gate_bound':False,
 'target_compiled':False,'runtime_verified':False},indent=2)+'\n')
print('Staged fallible free ABI/callers; pre-destructor retirement gate still unbound')
