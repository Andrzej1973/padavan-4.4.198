"""Early RC initial-OFF header closure before prepare-runtime adds headers."""
from pathlib import Path
import re,subprocess,tempfile,ast
here=Path(__file__).resolve().parent
source=(here/'prepare-rc.py').read_text()
a="(headers/'physical-stop-wire.h').write_bytes((local/'physical-stop-wire.h').read_bytes())"
b="(headers/'initial-off.h').write_bytes((local/'initial-off.h').read_bytes())"
assert source.count(a)==source.count(b)==1 and source.index(a)<source.index(b)
# Reconstruct headers actually listed by early preparation, without repository
# include paths which could silently satisfy a missing staged dependency.
available=set()
for n in ast.walk(ast.parse(source[:source.index(b)+len(b)])):
 if isinstance(n,ast.Constant) and isinstance(n.value,str) and n.value.endswith('.h') and '\n' not in n.value:
  available.add(n.value)
with tempfile.TemporaryDirectory(prefix='wr-initial-header-stage-') as d:
 root=Path(d);out=root/'wr-iot';out.mkdir()
 def copy(name):
  src=here/name;target=out/name
  assert src.is_file(),name
  target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(src.read_bytes())
  for include in re.findall(r'^#include "([^"]+)"',src.read_text(),re.M):
   dest=(target.parent/include).resolve()
   if dest.exists():continue
   if include.startswith('../shared-wifi/'):
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((here/include).read_bytes())
   else:
    assert include in available,('header absent from early staging',include)
    copy(include)
 copy('initial-off.h')
 # The implementation has dependencies not exposed by its public header.
 for include in re.findall(r'^#include "([^"]+)"',(here/'initial-off.c').read_text(),re.M):
  assert include in available,('implementation dependency absent from early staging',include)
  copy(include)
 unit=root/'check.c';unit.write_text('#include "wr-iot/initial-off.h"\nint main(void){return 0;}\n')
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-I'+d,str(unit),'-o',str(root/'check')],check=True)
print('PASS early initial-OFF staged header closure: physical RELEASE wire available before runtime; isolated include path, actual header compiled')
