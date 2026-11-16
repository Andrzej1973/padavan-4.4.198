"""Reproduce ABI901 include mapping with no repository include fallback."""
from pathlib import Path
import ast,re,subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'prepare-rc.py').read_text()
a=source.index("unit=(local/'start-runner.c')")
b=source.index("(rc/'wr-iot-start-runner.c').write_text",a)
ns={'local':here}
exec(compile(source[a:b],'<actual start runner preparation>','exec'),ns)
unit=ns['unit']
assert not re.findall(r'^#include "(?!wr-iot/)([^"]+)"',unit,re.M)
# Independent verifier must expect the same exact rewrite.
tree=ast.parse((here/'prepare-activation-header-check.py').read_text())
entry=next(ast.literal_eval(n) for n in ast.walk(tree) if isinstance(n,ast.Tuple) and n.elts and isinstance(n.elts[0],ast.Constant) and n.elts[0].value=='start-runner')
expected=(here/'start-runner.c').read_text()
for name in entry[1]:expected=expected.replace('#include "'+name+'"','#include "wr-iot/'+name+'"')
assert expected==unit
with tempfile.TemporaryDirectory(prefix='wr-runner-staged-') as d:
 root=Path(d);(root/'wr-iot').mkdir()
 for p in here.glob('*.h'):(root/'wr-iot'/p.name).write_bytes(p.read_bytes())
 (root/'shared-wifi').mkdir()
 for p in (here.parent/'shared-wifi').glob('*.h'):(root/'shared-wifi'/p.name).write_bytes(p.read_bytes())
 p=root/'runner.c';p.write_text(unit)
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-I'+str(root),'-fsyntax-only',str(p)],check=True)
print('PASS actual early RC start-runner include mapping and independent verifier agree; staged strict compilation without repository fallback; target pending')
