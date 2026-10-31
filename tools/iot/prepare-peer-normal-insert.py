#!/usr/bin/env python3
"""Count whole public insertion through unlocked finishing, preserving startup API."""
import argparse,hashlib,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
rel='mgmt/mgmt_entrytb.c';f=src/rel
if hashlib.sha256(f.read_bytes()).hexdigest()!='7cd8125a0ac1abea99038b25fb2e6e529bd911816733c5966f51a29b56b0bd2d':p.error('unreviewed insertion source')
s=f.read_text();start=s.index('MAC_TABLE_ENTRY *MacTableInsertEntry(');end=s.index('\n}',start)+2
old=s[start:end]
if old.count('return wr_iot_mac_insert_entry(pAd,pAddr,wdev,ent_type,OpMode,CleanAll,NULL,0);')!=1:p.error('changed public wrapper')
s=s[:start]+'#include "wr-iot-peer-normal-insert.inc"'+s[end:]
shutil.copytree(src,out);(out/rel).write_text(s,encoding='utf-8',newline='\n')
shutil.copyfile(Path(__file__).with_name('peer-normal-insert.inc'),out/'include/wr-iot-peer-normal-insert.inc')
print('Staged whole public insertion transaction; ordinary deletion remains unbound')
