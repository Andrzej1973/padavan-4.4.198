#!/usr/bin/env python3
"""Reconcile reviewed WDS open/close ownership into an isolated later candidate."""
import argparse
import hashlib
import json
import runpy
import shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();source=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or source==out or source in out.parents or out in source.parents:
    p.error('new separate output required')
here=Path(__file__).resolve().parent
name='ap/ap_wds_inf.c';data=(source/name).read_bytes()
if hashlib.sha256(data).hexdigest()!='9a20173fc99a049abd3ffa53e36ccd8c811acd45bfe104089f068babcf4ed958':
    p.error('unreviewed later WDS input')
start=b'INT WdsVirtualIF_open(PNET_DEV dev)';end=b'INT RT28xx_WDS_Remove(VOID *pAd)'
if data.count(start)!=1 or data.count(end)!=1:p.error('ambiguous WDS boundaries')
opening=runpy.run_path(str(here/'prepare-wds-open-owner-candidate.py'))['OPEN']
closing=runpy.run_path(str(here/'prepare-wds-close-owner-candidate.py'))['CLOSE']
changed=data[:data.index(start)]+opening+closing+data[data.index(end):]
anchor=b'/*#include "rt_config.h" */'
if changed.count(anchor)!=1:p.error('WDS include anchor differs')
changed=changed.replace(anchor,b'#include "rt_config.h"\n#include "virtual-open-claim.h"\n#include "aux-close-claim.h"',1)
# Do not replace shared later recovery/registry headers with old copies.
for n in ['radio-transition.h','interface-reference.h','interface-registry.h','virtual-open-claim.h']:
    expected = {'radio-transition.h':'a9372ddae073737f764917a2e7147b13c7a11e68e20a96e23b50f44059d01d2a'}
    matches = (hashlib.sha256((source/'include'/n).read_bytes()).hexdigest()==expected[n]
               if n in expected else (source/'include'/n).read_text()==(here/n).read_text())
    if not matches:
        p.error('shared current header mismatch: '+n)
gate=runpy.run_path(str(here/'prepare-aux-close-phase-gate-candidate.py'))['GATE']
reg_name='include/wr-iot-netdev-registration.inc'
reg=(source/reg_name).read_bytes()
marker=b'/* Use only when the attempted removal made no vendor/kernel mutation.'
if reg.count(marker)!=1:p.error('registration gate insertion changed')
reg=reg.replace(marker,gate+marker,1)
header_name='include/rtmp.h';header=(source/header_name).read_bytes()
marker=b'INT wr_iot_netdev_mark_removing(RTMP_ADAPTER *pAd, PNET_DEV dev);'
if header.count(marker)!=1:p.error('registration declaration changed')
header=header.replace(marker,marker+b'\nINT wr_iot_netdev_close_phase_idle(RTMP_ADAPTER *pAd, PNET_DEV dev);',1)
remove_name='ap/ap_wds.c';remove=(source/remove_name).read_bytes()
nl=b'\r\n' if b'\r\n' in remove else b'\n'
old=b'\t\t\tRtmpOSNetDevProtect(1);\n\t\t\tRtmpOSNetDevDetach(wdev->if_dev);'
new=b'\t\t\tRtmpOSNetDevProtect(1);\n\t\t\tRtmpOSNetDevClose(wdev->if_dev);\n\t\t\tif (wr_iot_netdev_close_phase_idle(pAd, wdev->if_dev) != NDIS_STATUS_SUCCESS) {\n\t\t\t\tRtmpOSNetDevProtect(0);\n\t\t\t\treturn NDIS_STATUS_FAILURE;\n\t\t\t}\n\t\t\tRtmpOSNetDevDetach(wdev->if_dev);'
old,new=old.replace(b'\n',nl),new.replace(b'\n',nl)
if remove.count(old)!=1:p.error('WDS remove sequence changed')
remove=remove.replace(old,new,1)
additional={reg_name:reg,header_name:header,remove_name:remove}
files={f.relative_to(source).as_posix():hashlib.sha256(f.read_bytes()).hexdigest()
       for f in source.rglob('*') if f.is_file()}
shutil.copytree(source,out);(out/name).write_bytes(changed)
for relative,data in additional.items():(out/relative).write_bytes(data)
shutil.copyfile(here/'aux-close-claim.h',out/'include/aux-close-claim.h')
result={f.relative_to(out).as_posix():hashlib.sha256(f.read_bytes()).hexdigest()
        for f in out.rglob('*') if f.is_file()}
expected=dict(files);expected[name]=hashlib.sha256(changed).hexdigest()
expected.update({n:hashlib.sha256(b).hexdigest() for n,b in additional.items()})
expected['include/aux-close-claim.h']=hashlib.sha256((here/'aux-close-claim.h').read_bytes()).hexdigest()
if result!=expected:raise SystemExit('unexpected reconciliation delta')
out.with_name(out.name+'-reconciliation.json').write_text(json.dumps({
 'input_sha256':files,'output_sha256':result,'changed_files':[name,*additional],
 'added_files':['include/aux-close-claim.h'],'production_installed':False,
 'target_compiled':False,'runtime_verified':False,
 'scope':'WDS only; other auxiliary families/removal remain separate'},indent=2)+'\n')
print('PASS isolated WDS ownership reconciliation; other families remain open')
