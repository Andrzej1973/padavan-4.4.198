#!/usr/bin/env python3
"""Bind exact published child-family snapshot before parent detach."""
import argparse,hashlib,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
rel='os/linux/pci_main_dev.c';f=src/rel
if hashlib.sha256(f.read_bytes()).hexdigest()!='020a6fcaa5a82ebaff3738c8b9ea6f163b2d45c9532d1e6f2fd33691add17288':p.error('unreviewed PCI source')
s=f.read_text();sig='static VOID DEVEXIT rt_pci_remove('
if s.count(sig)!=1:p.error('changed remove definition')
s=s.replace(sig,'#include "wr-iot-pci-child-snapshot.inc"\n'+sig,1)
anchor='\t\t/* A failed child detach leaves callbacks and references alive.'
if s.count(anchor)!=1:p.error('changed child detach anchor')
s=s.replace(anchor,'\t\tif (!wr_iot_pci_children_begin(adapter)) return;\n'+anchor,1)
shutil.copytree(src,out);(out/rel).write_text(s,encoding='utf-8',newline='\n')
shutil.copyfile(Path(__file__).with_name('pci-child-snapshot.inc'),out/'include/wr-iot-pci-child-snapshot.inc')
print('Staged published child-family begin snapshot; no family completion claims')
