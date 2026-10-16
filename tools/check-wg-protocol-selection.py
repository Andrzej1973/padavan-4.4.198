#!/usr/bin/env python3
"""Execute exact selector blocks with fake NVRAM/module availability; no networking."""
import os
from pathlib import Path
import subprocess
import tempfile
with tempfile.TemporaryDirectory(prefix='wg-selection-') as temp:
 root=Path(temp);module=root/'module'
 for name in ['wgc.sh','wgs.sh']:
  text=(Path(__file__).resolve().parent.parent/'overlay/padavan-4.4/trunk/user/amneziawg'/name).read_text()
  block=text[text.index('# Empty preserves'):text.index('IF_NAME=')]
  block=block.replace('/lib/modules/$(uname -r)/kernel/net/amneziawg',str(module))
  script=root/name
  script.write_text('nvram(){ printf "%s" "$VALUE"; }; logger(){ :; };\n'+block+
   'printf "%s %s" "$MODULE" "$WG"\n')
  for present in [False,True]:
   if present:module.mkdir()
   for value,wanted in [('wireguard','wireguard /usr/bin/wg-standard'),
                         ('amneziawg','amneziawg /usr/bin/awg'),
                         ('','amneziawg /usr/bin/awg' if present else 'wireguard /usr/bin/wg-standard'),
                         ('invalid',None)]:
    result=subprocess.run(['sh',str(script)],env=dict(os.environ,VALUE=value),capture_output=True,text=True,timeout=10)
    assert (result.returncode!=0 if wanted is None else result.returncode==0 and result.stdout==wanted),(name,value,result.stderr)
   if present:module.rmdir()
print('PASS host shell protocol selection; target and tunnel runtime remain unverified')
