#!/usr/bin/env python3
"""Exercise actual A/B evidence checker; synthetic ELF headers are not target proof."""
import subprocess,tempfile
from pathlib import Path
s=Path(__file__).with_name('ci-compile-psm-diagnostics.sh').read_text()
report=s.split("<<'PY'\n",1)[1].rsplit('\nPY',1)[0]
with tempfile.TemporaryDirectory(prefix='wr-psm-report-fixture-') as d:
 root=Path(d);driver=root/'driver';results=root/'results';results.mkdir()
 sources=['common/mt_ps.c','ap/ap.c','ap/ap_connect.c','tx_rx/txs.c','include/wr-iot-psm-diag.h']
 for name in sources:
  p=driver/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('fixture')
 elf=bytearray(32);elf[:6]=b'\x7fELF\x01\x01';elf[18]=8
 for mode in ['off','on']:
  (results/f'mt76x3_ap-psm-{mode}.ko').write_bytes(elf+mode.encode())
  commands=results/f'commands-{mode}';commands.mkdir();objects=results/f'objects-{mode}';objects.mkdir()
  for name in ['mt_ps','ap','ap_connect','txs']:
   (commands/(name+'.cmd')).write_text('cmd_x := gcc '+('-DWR_IOT_PSM_DIAG ' if mode=='on' else '')+'-c source.c\n')
   (objects/(name+'.o')).write_bytes(elf)
 def run(ok):
  r=subprocess.run(['python3','-c',report,str(results),str(driver)],capture_output=True,text=True)
  assert (r.returncode==0)==ok,r.stderr
 run(True)
 p=results/'commands-on/txs.cmd';original=p.read_text()
 p.unlink();run(False);p.write_text(original)
 p.write_text('cmd_x := gcc -c source.c\n# -DWR_IOT_PSM_DIAG\n');run(False);p.write_text(original)
 p=results/'objects-on/ap.o';original=p.read_bytes();p.write_bytes(b'not ELF');run(False);p.write_bytes(original)
 p=results/'mt76x3_ap-psm-on.ko';p.write_bytes((results/'mt76x3_ap-psm-off.ko').read_bytes());run(False)
print('PASS report checker: valid fixture, missing TU, flag only in comment, non-MIPS object, identical modules; no target build claim')
