#!/usr/bin/env python3
"""Regression: same catalogue output, denied pending boards, corrupt paths/profiles."""
import copy,json,shutil,sys,tempfile
from pathlib import Path
sys.dont_write_bytecode=True
from board_catalog import load,select
from audit import links
root=Path(__file__).resolve().parents[2]
original=json.loads((root/'boards.json').read_text())
with tempfile.TemporaryDirectory(prefix='wr-phase1-profile-check-') as d:
 out=Path(d)
 paths=[b['config'] for b in original['boards']]+['overlay/padavan-4.4/trunk/configs/boards/WR1200JS/'+n for n in ['board.h','board.mk','kernel-4.4.x.config']]
 paths+=['overlay/padavan-4.4/scripts/verify-wr1200js-image.py']
 paths+=['overlay/padavan-4.4/trunk/linux-4.4.x/arch/mips/boot/dts/ralink/'+n for n in ['wr1200js.dts','mt7621-spi-16m-wr1200js-layout.dtsi']]
 for name in paths:
  p=out/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/name,p)
 def write(data):(out/'boards.json').write_text(json.dumps(data))
 write(original);boards=load(out)
 assert select(boards,'all-supported')==[original['boards'][0]]
 assert select(boards,'wr1200js,wr1200js')==[original['boards'][0]]
 for selection in ['mi-mini','mi-4','future-board','wr1200js,mi-mini']:
  try:select(boards,selection)
  except ValueError:pass
  else:raise AssertionError('Admitted '+selection)
 variants=[]
 data=copy.deepcopy(original);data['boards'].append(copy.deepcopy(data['boards'][0]));variants.append(data)
 data=copy.deepcopy(original);data['boards'][0]['config']='../outside.config';variants.append(data)
 data=copy.deepcopy(original);data['boards'][1]['build_enabled']=True;variants.append(data)
 data=copy.deepcopy(original);data['boards'][0]['build_enabled']='true';variants.append(data)
 for data in variants:
  write(data)
  try:load(out)
  except ValueError:pass
  else:raise AssertionError('Invalid catalogue accepted')
 write(original);profile=out/original['boards'][0]['config'];old=profile.read_text();profile.write_text(old.replace('CONFIG_PRODUCT=MT7621','CONFIG_PRODUCT=MT7620'))
 try:load(out)
 except ValueError:pass
 else:raise AssertionError('Wrong SoC accepted')
 profile.write_text(old)
 for name,old_value,new_value in [
  ('overlay/padavan-4.4/trunk/linux-4.4.x/arch/mips/boot/dts/ralink/wr1200js.dts','YouHua WR1200JS','Wrong board'),
  ('overlay/padavan-4.4/trunk/linux-4.4.x/arch/mips/boot/dts/ralink/mt7621-spi-16m-wr1200js-layout.dtsi','0xf70000','0xf60000'),
  ('overlay/padavan-4.4/scripts/verify-wr1200js-image.py','16187392','16187391')]:
  path=out/name;before=path.read_text();assert old_value in before;path.write_text(before.replace(old_value,new_value))
  try:load(out)
  except ValueError:pass
  else:raise AssertionError('DTS/image drift accepted: '+name)
  path.write_text(before)
 board=out/'overlay/padavan-4.4/trunk/configs/boards/WR1200JS/board.mk';board.unlink()
 try:load(out)
 except ValueError:pass
 else:raise AssertionError('Missing required board source accepted')
 (out/'a.md').write_text('[valid](boards.json) [missing](absent.md) [external](https://example.com)')
 assert links(out,['a.md'])==['a.md -> absent.md']
print('PASS board catalogue compatibility, pending/unknown denial, duplicate/path/SoC/schema/missing-source failures and moved-link detection')
