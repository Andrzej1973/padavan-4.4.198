"""Actual static PID1 slot plus root controller with explicit child actors."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-cold-on-root.py')}
exec((here/'check-cold-on-root.py').read_text().split('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body']
a='int main(void){';assert body.count(a)==1
body=body.replace(a,'#include "cold-on-scheduler.c"\n'+a)
a='struct wr_iot_cold_root state={0},before;';assert body.count(a)==1
body=body.replace(a,'struct wr_iot_cold_root before;\n#define state cold_scheduler\n')
body=body.replace('wr_iot_cold_root_begin(root,&request,1)','wr_iot_rc_cold_on_begin(&request,1)')
body=body.replace('wr_iot_cold_root_step(root)','wr_iot_cold_on_step()').replace('wr_iot_cold_root_retire(root)','wr_iot_cold_on_retire()')
body=body.replace('assert(!wr_iot_cold_on_retire());','assert(wr_iot_cold_on_pending()&&!wr_iot_cold_on_retire());')
body=body.replace('retire=1;assert(wr_iot_cold_on_retire());','retire=1;assert(wr_iot_cold_on_retire()&&!wr_iot_cold_on_pending());')
with tempfile.TemporaryDirectory(prefix='wr-cold-static-slot-') as d:
 p=Path(d)/'check.c';p.write_text(body);binary=Path(d)/'check'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'cold-on-root.c'),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=20)
print('PASS actual static PID1 cold slot/root: both intents, stable child addresses, pending until checked retire, duplicate begin refused, failed release/retire retained, no observer re-begin or native fallback; children injected')
