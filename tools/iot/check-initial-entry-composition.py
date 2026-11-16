"""Actual INITIAL entry, selector, revalidation and physical claim."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-initial-selected-composition.py').read_text()
ns={'__file__':str(here/'check-initial-selected-composition.py')}
exec(compile(source[:source.index('\nwith tempfile.TemporaryDirectory(')],'<selected composition>','exec'),ns)
code=ns['code']
code=code.replace('assert(depth==1&&wr_iot_rc_shutdown.active&&n[0]==7&&!downs&&!initial_calls);', 'assert(depth==1&&n[0]==7&&!downs&&!initial_calls);')
for fault in range(1,6):
 code=code.replace('if(drift=='+str(fault), 'if(wr_iot_rc_shutdown.active&&drift=='+str(fault))
code=code.replace('probe_reads==2)wr_iot_rc_shutdown.pending', 'probe_reads==4)wr_iot_rc_shutdown.pending')
code=code.replace('return drift!=5;', 'return !wr_iot_rc_shutdown.active||drift!=5;')
a='int main(int argc,char **argv){'
assert a in code
code=code.replace(a,'int wr_iot_rc_restart_owned(void){return 0;}\n#include "initial-restart-entry.c"\n'+a,1)
a='assert(wr_iot_rc_physical_begin_initial_selected(&intent,nonce,&selected)&&saved_reads==1&&!downs&&!initial_calls);'
b='(void)intent;(void)nonce;(void)selected;assert(wr_iot_initial_restart_entry(1,1)==WR_RADIO_ENTRY_OWNED&&saved_reads==1&&!downs&&!initial_calls);'
assert a in code
code=code.replace(a,b,1)
with tempfile.TemporaryDirectory(prefix='wr-initial-entry-compose-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'physical-stop-session.c'),str(here/'radio-stop-fence.c'),str(here/'initial-restart-select.c'),'-o',str(b)],check=True)
 for args in [[],['1'],['2'],['3'],['4'],['5']]:subprocess.run([str(b)]+args,check=True,timeout=15)
print('PASS actual INITIAL entry/selector/physical claim: double fresh selection, exact claim-time epoch/generation/serial; post-selection drift/TERM/read failure owned cleanup without ARM/DOWN or legacy fallback; driver/software actors')
