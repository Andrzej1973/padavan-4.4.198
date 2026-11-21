from pathlib import Path
import ast,re,subprocess,tempfile,json,hashlib,datetime
here=Path(__file__).resolve().parent;root=here;strings=set()
for name in ('prepare-rc.py','prepare-runtime.py'):
 source=(root/name if (root/name).exists() else here/name).read_text()
 strings.update(n.value for n in ast.walk(ast.parse(source)) if isinstance(n,ast.Constant) and isinstance(n.value,str))
with tempfile.TemporaryDirectory(prefix='wr-initial-shutdown-headers-') as d:
 dest=Path(d)/'wr-iot';dest.mkdir()
 def stage(name):
  target=dest/name
  if target.exists():return
  if name=='../shared-wifi/validate.h':
   assert "(shared/'validate.h').write_bytes((local.parent/'shared-wifi/validate.h').read_bytes())" in (here/'prepare-rc.py').read_text()
  else:assert name in strings,name
  source=root/name if (root/name).exists() else here/name
  target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
  for dep in re.findall(r'^#include "([^"]+)"',source.read_text(),re.M):stage(dep)
 for name in ('initial-off.h','rc-backend.h','rc-initial-stop.h','initial-shutdown-owner.h'):stage(name)
 for header in ('initial-off.h','rc-backend.h','rc-initial-stop.h','initial-shutdown-owner.h'):
  single=Path(d)/'single.c';single.write_text('#include "wr-iot/'+header+'"\n')
  subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-fsyntax-only','-I'+d,str(single)],check=True)
 unit=Path(d)/'check.c';unit.write_text('#include "wr-iot/initial-off.h"\n#include "wr-iot/rc-backend.h"\n#include "wr-iot/rc-initial-stop.h"\nstruct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;\nint main(void){return 0;}\n')
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-I'+d,str(unit),'-o',d+'/check'],check=True)
print('PASS actual routed INITIAL fixture: check-initial-shutdown-headers.py; external adapters injected, target/runtime pending')
