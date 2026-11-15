"""Execute generated INITIAL_OFF adapter retirement guard and PID return."""
from pathlib import Path
import runpy,subprocess,tempfile,shutil
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-physical-stop-terminal-free.py')}
s=(here/'check-physical-stop-terminal-free.py').read_text()
exec(compile(s[:s.index('\nwith tempfile.TemporaryDirectory(')],'<free fixture>','exec'),ns)
transform=runpy.run_path(str(here/'physical-initial-storage.py'))['compose']
header='#include "physical-stop-terminal-types.h"\nstruct wr_iot_physical_stop_terminal wr_iot_physical_terminal;'
init='NdisZeroMemory(&pAd->wr_iot_physical_terminal,sizeof(pAd->wr_iot_physical_terminal));'
_,_,fragment=transform(header,init,ns['fragment'])
code=ns['code'].replace('#include <assert.h>','#include <assert.h>\n#include <stddef.h>',1).replace('#include "physical-stop-terminal-types.h"','#include "physical-stop-terminal-types.h"\n#include "physical-initial-types.h"\n#include "physical-initial-terminal-types.h"',1)
code=code.replace(' struct wr_iot_physical_rebind_probe wr_iot_physical_rebind_probe;', ' struct wr_iot_physical_rebind_probe wr_iot_physical_rebind_probe;\n struct wr_iot_physical_initial_record wr_iot_physical_initial;\n struct wr_iot_physical_initial_terminal wr_iot_physical_initial_terminal;',1)
needle=' ad.wr_iot_physical_terminal.owner=&identity;ad.wr_iot_physical_terminal.ready=1;'
code=code.replace(needle,r'''
 struct pid initial_pid={2};
 ad.wr_iot_physical_initial.task=(void *)2;
 assert(!wr_iot_raw_recovery_free_fence(&ad)&&!puts);
 ad.wr_iot_physical_initial.task=NULL;
 ad.wr_iot_physical_initial.status=WR_STOP_COMPLETE;
 assert(!wr_iot_raw_recovery_free_fence(&ad)&&!puts);
 ad.wr_iot_physical_initial_terminal.owner=&initial_pid;
 assert(!wr_iot_raw_recovery_free_fence(&ad)&&!puts&&initial_pid.refs==2);
 ad.wr_iot_physical_initial_terminal.ready=1;
 assert(wr_iot_raw_recovery_free_fence(&ad)&&puts==1&&initial_pid.refs==1);
 assert(!ad.wr_iot_physical_initial_terminal.owner);
 /* Model fresh storage for the inherited ordinary-CLOSE regression below. */
 ad.wr_iot_physical_initial.status=0;puts=0;
'''+needle,1)

with tempfile.TemporaryDirectory(prefix='wr-stop-terminal-free-') as d:
 root=Path(d);(root/'raw-free-physical.inc').write_text(fragment)
 shutil.copyfile(here/'main-reopen-admission.h',root/'wr-iot-main-reopen-admission.h')
 c=root/'check.c';c.write_text(code)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(root),'-I'+str(here),str(c),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True)
print('PASS generated initial free guard: active record/unready cache retain, complete cache PID returned once outside lock, ordinary CLOSE guard preserved; native free not executed')
