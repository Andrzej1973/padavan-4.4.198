"""Compile WPIQ client/session only from runtime-declared staged payload."""
from pathlib import Path
import ast,re,subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'prepare-runtime.py').read_text()
strings={n.value for n in ast.walk(ast.parse(source)) if isinstance(n,ast.Constant) and isinstance(n.value,str)}
early=ast.parse((here/'prepare-rc.py').read_text())
strings.update(n.value for n in ast.walk(early) if isinstance(n,ast.Constant) and isinstance(n.value,str))
link=(here/'compile-runtime-link.sh').read_text()
for unit,symbol in (('physical-initial-client','wr_iot_physical_initial_call'),('physical-initial-session','wr_iot_initial_physical_session_begin'),('physical-initial-session','wr_iot_initial_physical_session_advance'),('rc-initial-stop','wr_iot_rc_initial_stop_begin'),('rc-initial-stop','wr_iot_rc_initial_stop_step'),('rc-initial-stop','wr_iot_rc_initial_stop_released'),('rc-backend','wr_iot_rc_backend_initial_request'),('rc-backend','wr_iot_rc_backend_prepared_initial_request'),('initial-off','wr_iot_initial_off_physical_request')):
 assert unit+':'+symbol in link,('missing target symbol gate',unit,symbol)
for name in ('physical-initial-client','physical-initial-session','rc-initial-stop'):
 assert name in strings,('runtime object missing',name)
with tempfile.TemporaryDirectory(prefix='wr-initial-runtime-stage-') as d:
 root=Path(d)/'wr-iot';root.mkdir()
 def stage(name):
  out=root/name
  if out.exists():return
  if name=='../shared-wifi/validate.h':
   assert "(shared/'validate.h').write_bytes((local.parent/'shared-wifi/validate.h').read_bytes())" in (here/'prepare-rc.py').read_text()
  else:assert name in strings,('header missing from runtime declaration',name)
  out.parent.mkdir(parents=True,exist_ok=True)
  out.write_bytes((here/name).read_bytes())
  for include in re.findall(r'^#include "([^"]+)"',out.read_text(),re.M):stage(include)
 for name in ('physical-initial-client','physical-initial-session','rc-initial-stop'):
  unit=root/(name+'.c');unit.write_bytes((here/(name+'.c')).read_bytes())
  for include in re.findall(r'^#include "([^"]+)"',unit.read_text(),re.M):stage(include)
  subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-I'+str(root),'-c',str(unit),'-o',str(root/(name+'.o'))],check=True)
print('PASS runtime-declared WPIQ client/session object/header closure compiles without repository include fallback; actual SDK Make/target linkage pending')
