#!/usr/bin/env python3
"""Require terminal release receipt and peer fence before controller destructors."""
import argparse,hashlib,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
rel='common/rtmp_init.c';f=src/rel
if hashlib.sha256(f.read_bytes()).hexdigest()!='947b4b3687c2177cd47622b3660601ddef3ad37c66ec579f4b6fdf59ba146094':p.error('unreviewed controller source')
s=f.read_text();sig='BOOLEAN RtmpRaDevCtrlExit(IN VOID *pAdSrc)'
if s.count(sig)!=1:p.error('changed controller definition')
start=s.index(sig);end=s.index('\n}',start)+2;body=s[start:end]
anchor='\tINT index;'
if body.count(anchor)!=1:p.error('changed controller declarations')
body=body.replace(anchor,anchor+'\n\tif (!wr_iot_adapter_release_begin(pAd)) return FALSE;',1)
s=s[:start]+'#include "wr-iot-peer-adapter-release.inc"\n'+body+s[end:]
shutil.copytree(src,out);(out/rel).write_text(s,encoding='utf-8',newline='\n')
shutil.copyfile(Path(__file__).with_name('peer-adapter-release.inc'),out/'include/wr-iot-peer-adapter-release.inc')
print('Staged pre-destructor terminal-receipt/peer fence; receipt production and cold unwind remain open')
