#!/usr/bin/env python3
"""Synthetic policy fixtures, not ELF/image build proof."""
import importlib.util
import json
from pathlib import Path
import tempfile

here=Path(__file__).parent
spec=importlib.util.spec_from_file_location('cake_image',here/'verify-cake-image.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
manifest=json.loads((here/'board-capabilities/wr1200js-cake.json').read_text())
with tempfile.TemporaryDirectory(prefix='wr-cake-image-gate-') as tmp:
 root=Path(tmp)
 def write(name,value):
  p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(value);return p
 write('trunk/.config','CONFIG_FIRMWARE_INCLUDE_SQM=y\n')
 kernel=write('trunk/linux-4.4.x/.config','\n'.join(k+'='+v for k,v in manifest['kernel_required'].items()))
 defaults=write('trunk/user/shared/defaults.c','{ "sqm_enable", "0" },')
 write('trunk/user/rc/services.c','if (nvram_get_int("sqm_enable") != 1 || get_ap_mode()) return;')
 for name in manifest['modules']:write('trunk/romfs/lib/modules/4.4.198/'+name,'fixture, not ELF')
 for name in ['bin/tc','bin/ip']:write('trunk/romfs/'+name,'fixture')
 page=write('trunk/romfs/www/Advanced_SQM.asp',(here.parent/'overlay/padavan-4.4/ports/sqm/Advanced_SQM.asp').read_text())
 script=root/'trunk/romfs/usr/lib/sqm/run.sh';script.parent.mkdir(parents=True)
 script.write_bytes((here.parent/'overlay/padavan-4.4/ports/sqm/run.sh').read_bytes())
 assert all(m.check(root)['checks'].values())
 cake=root/'trunk/romfs/lib/modules/4.4.198/sch_cake.ko';cake.unlink()
 assert not m.check(root)['checks']['sch_cake.ko'];cake.write_text('fixture')
 defaults.write_text('{ "sqm_enable", "1" },');assert not m.check(root)['checks']['factory_off']
 defaults.write_text('{ "sqm_enable", "0" },')
 kernel.write_text(kernel.read_text()+'\nCONFIG_DEFAULT_NET_SCH="cake"\n')
 assert not m.check(root)['checks']['not_default_qdisc']
print('PASS CAKE presence/default gate accepts fixture and rejects missing module, factory ON and default CAKE qdisc')
