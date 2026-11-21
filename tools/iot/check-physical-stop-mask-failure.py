"""Actual physical STOP retains guard and desired state across failed unmask."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
s=(here/'check-rc-physical-stop.c').read_text()
anchor='#include "rc-physical-stop.c"'
wrapper=r'''
static int fail_restore;
static int test_mask(int op,const sigset_t *set,sigset_t *old)
{
 if(op==SIG_SETMASK&&fail_restore)return -1;
 return sigprocmask(op,set,old);
}
#define sigprocmask test_mask
#include "radio-stop-fence.c"
#undef sigprocmask
'''
assert s.count(anchor)==1
s=s.replace(anchor,wrapper+anchor)
anchor=' outcome=WR_PHYSICAL_CALL_ACKNOWLEDGED;wr_iot_rc_physical_step();\n assert(!depth'
replacement=''' outcome=WR_PHYSICAL_CALL_ACKNOWLEDGED;
 strcpy(physical.quiesce.desired.password,"retained until cleanup");
 fail_restore=1;wr_iot_rc_physical_step();
 assert(depth==1&&physical.guard==1&&!physical.result&&physical.finishing==1);
 assert(wr_iot_rc_shutdown.active&&!shutdowns&&physical.fence.owner==getpid());
 assert(!strcmp(physical.quiesce.desired.password,"retained until cleanup"));
 assert(!wr_iot_rc_physical_take(&out));
 int completed_calls=calls;
 fail_restore=0;wr_iot_rc_physical_step();assert(calls==completed_calls);
 assert(!depth'''
assert s.count(anchor)==1
s=s.replace(anchor,replacement)
with tempfile.TemporaryDirectory(prefix='wr-stop-mask-') as d:
 p=Path(d)/'check.c';p.write_text(s);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'physical-stop-session.c'),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS physical STOP mask fault: guard/desired/result retained, same-fence retry publishes and wipes before real SIGTERM, no driver replay, terminal take once; transport injected')
