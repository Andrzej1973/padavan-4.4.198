"""Actual post-RELEASE observation with real release/origin/registry predicates."""
from pathlib import Path
import runpy,subprocess,tempfile,shutil
here=Path(__file__).resolve().parent
base=runpy.run_path(str(here/'check-physical-stop-release.py'))
context=base['context'].replace('int main(void){','#define NdisZeroMemory(p,n) memset(p,0,n)\n#include "physical-stop-query.inc"\n#include "physical-stop-terminal-replace.inc"\n#include "physical-stop-cancel.inc"\n#include "physical-stop-terminal-down.inc"\n#include "physical-stop-handler.inc"\nint main(void){')
body=base['body'];a='   struct wr_iot_physical_stop_origin saved_origin=ad.wr_iot_physical_terminal.origin;'
assert body.count(a)==1
body=body.replace(a,a+r'''
   {
    struct wr_iot_physical_stop_request q=rel;q.action=WR_STOP_QUERY;
    RTMP_ADAPTER before=ad;

    assert(!wr_iot_physical_stop_handle(&ad,&main_dev,&q,wire,64));
    assert(wr_iot_physical_stop_response_decode(&response,wire,64,&q)&&response.status==WR_STOP_COMPLETE);
    assert(!memcmp(&before,&ad,sizeof(ad))&&modules==1&&tasks==1&&devices==1);
    q.nonce[0]++;assert(wr_iot_physical_stop_handle(&ad,&main_dev,&q,wire,64)==-EAGAIN);q.nonce[0]--;
    ad.wr_iot_transition.epoch++;assert(wr_iot_physical_stop_handle(&ad,&main_dev,&q,wire,64)==-EAGAIN);ad.wr_iot_transition.epoch--;
    ad.wr_iot_transition.main_ready=1;assert(wr_iot_physical_stop_handle(&ad,&main_dev,&q,wire,64)==-EAGAIN);ad.wr_iot_transition.main_ready=0;
    ad.wr_iot_peer_table_owner.poisoned=1;assert(wr_iot_physical_stop_handle(&ad,&main_dev,&q,wire,64)==-EAGAIN);ad.wr_iot_peer_table_owner.poisoned=0;
    assert(!wr_iot_physical_stop_handle(&ad,&main_dev,&q,wire,64));
    assert(!memcmp(&before,&ad,sizeof(ad))&&identity.refs==2);
   }
''')
with tempfile.TemporaryDirectory(prefix='wr-terminal-down-') as d:
 root=Path(d);inc=root/'include';inc.mkdir()
 for p in here.glob('*.h'):shutil.copyfile(p,inc/p.name)
 for n in ('radio-transition.h','radio-transition-api.h'):
  p=inc/n;p.write_text(p.read_text().replace('virtual_down_stage,virtual_up_stage;','virtual_down_stage,virtual_up_stage,mt_radio_off_stage;'))
 p=root/'check.c';p.write_text(base['base']['base']['base']['prefix']+context+body)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(inc),'-I'+str(here),str(p),'-o',str(root/'check')],check=True)
 subprocess.run([str(root/'check')],check=True,timeout=15)
print('PASS actual post-RELEASE DOWN observation: PID/nonce/tuple plus current Main release/registry/epoch/peer idle; stale/reopened/poisoned refuse, no adapter mutation/ref replay; kernel actors injected, handler bound; ioctl transport/target/device separate')
