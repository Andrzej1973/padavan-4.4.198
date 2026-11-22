"""Actual released ON owner -> physical OFF admission/session/fence composition."""
from pathlib import Path
import subprocess,tempfile,re,os
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-radio-on-owner.py')}
exec((here/'check-radio-on-owner.py').read_text().rsplit('with tempfile.TemporaryDirectory(',1)[0],ns)
owner=ns['body'].replace('for(int fault=0;fault<3;fault++)','for(int fault=1;fault<2;fault++)')
a=owner.index('    struct wr_iot_radio_stop_fence off_fence={0};')
b=owner.index('    wr_iot_service_guard_leave(1);assert(wr_iot_radio_stop_fence_end(&off_fence));',a)
b+=len('    wr_iot_service_guard_leave(1);assert(wr_iot_radio_stop_fence_end(&off_fence));')
owner=owner[:a]+'''    assert(physical_fixture_stop());
    assert(!on_owner.owner&&!wr_iot_rc_shutdown.radio_on_owned&&!wr_iot_radio_on_pending());
'''+owner[b:]
owner='int physical_fixture_stop(void);\n'+owner+'\nint on_fixture_guard_depth(void){return depth;}\n'
physical=(here/'check-rc-physical-stop.c').read_text().split('int main(void)',1)[0]
def remove(src,name):
 m=re.search(r'^int '+re.escape(name)+r'\(',src,re.M)
 if not m:m=re.search(r'^void '+re.escape(name)+r'\(',src,re.M)
 assert m,name
 i=src.index('{',m.start());level=1;j=i+1
 while level:
  level+=(src[j]=='{')-(src[j]=='}');j+=1
 return src[:m.start()]+src[j:]
for name in ['wr_iot_radio_on_off_ready','wr_iot_radio_on_off_handoff','wr_iot_service_guard_enter','wr_iot_service_guard_leave','wr_iot_rc_radio_on_saved_request']:
 physical=remove(physical,name)
physical=physical.replace('struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;','extern struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;')
physical=physical.replace('static int depth,','int on_fixture_guard_depth(void);\n#define depth on_fixture_guard_depth()\nstatic int ',1)
physical+=r'''
#include <stdlib.h>
static void tail_routed_signal(int sig){
 if(wr_iot_rc_shutdown_note(sig))return;
 assert(sig==SIGTERM&&!physical.owner&&!depth&&!wr_iot_rc_shutdown.radio_on_owned);shutdowns++;
}
int physical_fixture_stop(void){
 (void)handler;(void)guard_fail;
 struct wr_iot_rc_physical_intent stop={0},out={0};
 struct wr_iot_control_request off={.id="11111111111111111111111111111111",.created=1};
 assert(wr_iot_radio_on_off_ready()&&wr_iot_rc_shutdown.radio_on_owned&&!depth);
 int routed=getenv("WR_ON_TAIL_ROUTED")!=NULL;
 if(routed){
  struct sigaction sa={0};sa.sa_handler=tail_routed_signal;sigemptyset(&sa.sa_mask);assert(!sigaction(SIGTERM,&sa,NULL));
  wr_iot_rc_shutdown.normal_route_armed=1;wr_iot_rc_shutdown.normal_route_requested=SIGTERM;
  assert(wr_iot_rc_physical_begin_routed_shutdown(&off));
 }else assert(wr_iot_rc_physical_begin_quiesce(&stop,&off));
 assert(!wr_iot_rc_shutdown.radio_on_owned&&physical.owner==getpid()&&depth==1&&wr_iot_rc_shutdown.active);
 query_status=WR_STOP_COMPLETE;
 for(int i=0;i<40&&wr_iot_rc_physical_pending();i++)wr_iot_rc_physical_step();
 assert(!wr_iot_rc_physical_pending()&&!depth&&!wr_iot_rc_shutdown.active&&downs==1);
 if(routed){
  assert(wr_iot_rc_shutdown.normal_route_requested==SIGTERM&&!shutdowns);
  assert(wr_iot_rc_physical_shutdown_release(off.id,off.created)&&shutdowns==1&&!physical.owner);
  return 1;
 }
 return wr_iot_rc_physical_take(&out)==1&&!out.restart&&!out.radio_on;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-on-tail-physical-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 (root/'owner.c').write_text('#define WR_IOT_IAPP_POLICY_H\n#define WR_IOT_IAPP_POLICY_PREPARED 1\n'+owner)
 (root/'physical.c').write_text(physical)
 cmd=['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(root/'owner.c'),str(root/'physical.c'),str(here/'physical-stop-session.c'),'-o',str(root/'check')]
 subprocess.run(cmd,check=True)
 for routed in (False,True):
  env=dict(os.environ);env.pop('WR_ON_TAIL_ROUTED',None)
  if routed:env['WR_ON_TAIL_ROUTED']='1'
  subprocess.run([str(root/'check'),d],check=True,timeout=20,env=env)
print('PASS actual failed-IAPP ON root -> physical pure-OFF fence/guard handoff -> real session RELEASE and one DOWN in explicit/routed modes; shared guard/exclusion, backend/driver adapters injected; no router acceptance')
