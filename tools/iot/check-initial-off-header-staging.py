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
 # Compile the actual implementation from staged files, not just its public
 # header. A private C-file include caused ABI897 even though header checks passed.
 # Match prepare-rc's root-level unit and exact include rewriting. Adding a
 # wr-iot include path here would hide missing transformation entries (ABI898).
 block=source[source.index("unit=(local/'initial-off.c')"):source.index("(rc/'wr-iot-initial-off.c')")]
 tree=ast.parse(block)
 names=next(ast.literal_eval(node.iter) for node in ast.walk(tree) if isinstance(node,ast.For))
 transformed=(here/'initial-off.c').read_text()
 for name in names:transformed=transformed.replace('#include "'+name+'"','#include "wr-iot/'+name+'"',1)
 implementation=root/'wr-iot-initial-off.c';implementation.write_text(transformed)
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-I'+d,'-c',str(implementation),'-o',str(root/'initial-off.o')],check=True)
print('PASS early initial-OFF staged header closure: physical RELEASE and shutdown dependencies available before runtime; actual header and C implementation compiled using staged paths only')
