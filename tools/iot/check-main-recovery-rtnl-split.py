#!/usr/bin/env python3
"""Execute extracted recovery close and assert its physical call has no RTNL."""
import argparse,subprocess,tempfile,re
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args();here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='wr-main-rtnl-split-') as d:
 c=Path(d)/'check.c'
 subprocess.run(['python3',str(here/'prepare-main-close-check.py'),str(c),'--candidate',str(a.candidate)],check=True)
 s=c.read_text();marker='static int held,pins,preclose,down_calls,down_result,wakes;';assert s.count(marker)==1
 s=s.replace(marker,marker+'''
static int rtnl=1,in_recovery;
static void rtnl_unlock(void){assert(rtnl&&!held&&pins>0);rtnl=0;}
''')
 s=s.replace('assert(ad&&ticket&&!held);down_calls++;','assert(ad&&ticket&&!held);if(in_recovery)assert(!rtnl);down_calls++;')
 # Existing physical-close faults and exact-ticket retries exercise both success
 # and retained failure through the actual generated executor.
 s,n=re.subn(r'wr_iot_main_recovery_execute\((&\w+)\)',r'run_recovery(\1)',s);assert n==3
 marker='static void setup(struct adapter *ad,struct net_device *dev,'
 wrapper='''static int run_recovery(PRTMP_ADAPTER ad){
 int released=0,result;
 rtnl=1;in_recovery=1;
 result=wr_iot_main_recovery_execute(ad,&released);
 assert((released&&!rtnl)||(!released&&rtnl));
 in_recovery=0;rtnl=1;return result;
}
'''
 assert s.count(marker)==1;s=s.replace(marker,wrapper+marker)
 marker=' puts("PASS partial main close:'
 assert s.count(marker)==1
 s=s.replace(marker,''' setup(&deferred,&e,&peer,1);
 assert(run_recovery(&deferred)==-1&&rtnl==1&&pins==1);
'''+marker)
 c.write_text(s)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.candidate/'include'),'-I'+str(here),str(c),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True)
print('PASS actual recovery continuation: RTNL released with pin held, exact-ticket retry, retained failure and one module release')
