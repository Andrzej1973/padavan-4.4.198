from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
s=(here/'check-start-commit.c').read_text().replace('#include "start-commit.h"','#include "rebind-commit.h"').replace('#include "start-commit.c"','#include "rebind-commit.c"')
s=s.replace('struct wr_iot_start_admission owner={.admitted=1,.staged=1,.mutation_started=1,.idle={1,2,1}};', 'struct wr_iot_rebind_start rebind={.owner=getpid(),.identity={1,2},.open_id={1},.admission={.reopened=2,.admitted=1,.staged=1,.mutation_started=1}};')
s=s.replace('owner.', 'rebind.admission.').replace('struct wr_iot_open_controller open=', 'struct wr_iot_rebind_open_controller open=').replace('WR_IOT_OPEN_CONFIRMED','WR_REBIND_OPEN_CURRENT')
s=s.replace('wr_iot_start_commit_step(&state,&owner,','wr_iot_rebind_commit_step(&state,&rebind,')
anchor='  assert(!wr_iot_rebind_commit_step(&state,&rebind,&network,&open,&request));'
s=s.replace(anchor,'''  open.phase=WR_REBIND_OPEN_RETAINED;
  assert(!wr_iot_rebind_commit_step(&state,&rebind,&network,&open,&request)&&!commits);
  open.phase=WR_REBIND_OPEN_CURRENT;
'''+anchor,1)
with tempfile.TemporaryDirectory(prefix='wr-rebind-commit-') as d:
 src=Path(d)/'check.c';out=Path(d)/'check';src.write_text(s)
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(src),'-o',str(out)],check=True)
 subprocess.run([str(out)],check=True)
print('PASS rebind commit refuses recovery-only state; exact OPEN identity/network, one DNS commit, uncertainty retained, snapshot suspend failures; actors injected')
