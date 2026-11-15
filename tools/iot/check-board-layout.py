"""Only tracked Git inputs supply WR1200JS image layout validation."""
from pathlib import Path
import subprocess,tempfile,runpy
here=Path(__file__).resolve().parent
validate=runpy.run_path(str(here/'verify-board-layout.py'))['validate_wr_layout']
base='overlay/padavan-4.4/trunk/linux-4.4.x/arch/mips/boot/dts/ralink/'
inputs=[base+'wr1200js.dts',base+'mt7621-spi-16m-wr1200js-layout.dtsi','overlay/padavan-4.4/scripts/verify-wr1200js-image.py']
with tempfile.TemporaryDirectory(prefix='wr-tracked-layout-') as d:
 root=Path(d)
 for name in inputs:
  data=subprocess.check_output(['git','show','HEAD:'+name],cwd=here.parent.parent)
  p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 assert validate(root)['firmware']==(0x50000,0xf70000)
 assert not (root/'tools/repository').exists()
 layout=root/inputs[1];good=layout.read_bytes()
 layout.write_bytes(good.replace(b'0xf70000',b'0xf60000'))
 try:validate(root)
 except ValueError:pass
 else:raise AssertionError('Partition drift accepted')
 layout.write_bytes(good)
 verifier=root/inputs[2];good=verifier.read_bytes();verifier.write_bytes(good.replace(b'16187392',b'16187391'))
 try:validate(root)
 except ValueError:pass
 else:raise AssertionError('Verifier limit drift accepted')
 assert "tools/repository/board_catalog.py" not in (here/'ci-stage-candidate-romfs.sh').read_text()
print('PASS WR layout from tracked Git files only: no untracked board catalogue dependency, exact DTS/partition/size gates, drift refuses')
