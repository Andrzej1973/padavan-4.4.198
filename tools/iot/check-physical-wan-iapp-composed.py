from pathlib import Path
root=Path(__file__).resolve().parent
text=(root/'check-physical-resume-composed.py').read_text()
extra=r'''
a='#include "restart-resume.c"'
assert a in backend
backend=backend.replace('static volatile sig_atomic_t physical_replays;', 'static int expected_iapp_shutdown;static volatile sig_atomic_t physical_replays;')
backend=backend.replace('assert(!depth&&!wr_iot_rc_shutdown.active);physical_replays++;', 'assert(!depth&&!wr_iot_rc_shutdown.active);if(expected_iapp_shutdown)assert(backend.phase==WR_IOT_OWNER_OFF&&backend.stop.complete);physical_replays++;')
backend=backend.replace(a,r"""
#include <sys/wait.h>
#include "restart-wan-followup.h"
static int wan_plans,wan_dispatches,wan_leds,wan_observer_holds;
int wr_iot_rc_restart_wan_plan(int on,enum wr_iot_wan_followup *out){assert(on==1&&wr_iot_rc_shutdown.active);wan_plans++;*out=WR_WAN_RECONNECT;return 1;}
int wr_iot_rc_restart_wan_current(int on,enum wr_iot_wan_followup plan){return on==1&&plan==WR_WAN_RECONNECT;}
void wr_iot_rc_restart_wan_submit(enum wr_iot_wan_followup plan){
 assert(plan==WR_WAN_RECONNECT&&!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending);
 physical_fixture_terminal();wan_dispatches++;assert(wan_dispatches==1);filter_ok=0;
}
int wr_iot_rc_restart_led_on(void){assert(wan_dispatches==1&&filter_ok&&!wr_iot_rc_shutdown.active);wan_leds++;return 1;}
#include "restart-resume.c"
""")
backend=backend.replace('for(unsigned i=0;i<100;i++){','for(unsigned i=0;i<10000;i++){',1)
backend=backend.replace('int finish=!strcmp(mode,"finish"),reached=0,injected=0;', 'int finish=!strncmp(mode,"finish",6),reached=0,injected=0,late_signal=0,late_unmask=0;')
a='  if(finish&&pump.phase==WR_RESUME_FINISH&&!injected){'
assert a in backend
backend=backend.replace(a,r"""
  if(finish&&!strcmp(mode,"finish_pending")&&pump.phase==WR_RESUME_WAN&&pump.terminal.attempted&&!late_signal){
   expected_iapp_shutdown=1;assert(!raise(SIGTERM));late_signal=1;
  }
  if(late_signal&&wr_iot_rc_shutdown.pending&&pump.phase==WR_RESUME_WAN){
   struct wr_iot_control_request off={.id="09000000000000000000000000000000",.created=21};
   assert(wr_iot_restart_resume_shutdown(&pump,&off));
   close_result=progress_result=release_result=WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;fail_unmask=1;
  }
  if(pump.phase==WR_RESUME_POSTWAN_SHUTDOWN){
   if(pump.shutdown.complete&&!late_unmask){
    assert(backend.phase==WR_IOT_OWNER_OFF&&pump.initial_receipt.open_token&&!physical_replays&&pump.terminal.child&&pump.terminal.guard==1);
    fail_unmask=0;late_unmask=1;
   }
   usleep(1000);
  }
  if(pump.phase==WR_RESUME_CANCELLED)break;
  if(finish&&pump.phase==WR_RESUME_WAN){
   if(wan_dispatches&&!filter_ok){
    assert(wan_dispatches==1&&!wan_leds&&!pump.terminal.owner);
    if(++wan_observer_holds==3)filter_ok=1;
   }
   usleep(1000);
  }
"""+a)
a='  assert(pump.initial_receipt.open_token&&wr_iot_rc_initial_restart_postrelease_current(&pump.initial_receipt));'
assert a in backend
backend=backend.replace(a,a+r"""
  assert(wan_plans==1&&wan_dispatches==1&&wan_leds==1&&wan_observer_holds==3);
  assert(pump.restore.iapp.attempted&&pump.restore.iapp.fd==-1&&pump.restore.iapp.result==1);
  assert(pump.terminal.attempted&&pump.terminal.result==1&&!pump.terminal.child&&!pump.terminal.guard);
  int child_status;assert(waitpid(-1,&child_status,0)>0&&WIFEXITED(child_status)&&WEXITSTATUS(child_status)==0);
""")
'''
extra+='\nbackend=backend.replace(" parent_fixture_dispose(&pump.restore);return 0;", " parent_fixture_dispose(&pump.restore);struct wr_iot_activation_owner kept=backend;assert(wr_iot_restart_resume_retire(&pump));struct wr_iot_restart_resume empty={0};assert(!memcmp(&pump,&empty,sizeof(pump))&&!memcmp(&kept,&backend,sizeof(backend)));return 0;")\n'
extra+='\nbackend=backend.replace(\'if(finish){\\n  assert(injected&&pump.phase==WR_RESUME_DONE\', \'if(finish&&!strcmp(mode,"finish_pending")){\\n  assert(late_signal&&late_unmask&&pump.phase==WR_RESUME_CANCELLED&&physical_replays==1);\\n  assert(backend.phase==WR_IOT_OWNER_OFF&&!backend.start.input.request.password[0]);\\n  assert(wan_plans==1&&wan_dispatches==1&&wan_leds==1);\\n  assert(wr_iot_restart_resume_step(&pump)==-1);physical_fixture_terminal();\\n  int st;assert(waitpid(-1,&st,0)>0&&WIFEXITED(st)&&WEXITSTATUS(st)==0);\\n }else if(finish){\\n  assert(injected&&pump.phase==WR_RESUME_DONE\')\n'
anchor="anchor='\\nwith tempfile.TemporaryDirectory('"
assert anchor in text
text=text.replace(anchor,'inject+='+repr(extra)+'\n'+anchor,1)
anchor="exec(compile(source,str(Path(__file__)), 'exec'),{'__file__':__file__})"
assert anchor in text
staging=r'''
source=source.replace("n in ('start-runner.c','start-closed-rollback.c','radio-stop-fence.c')", "n in ('start-runner.c','start-closed-rollback.c','radio-stop-fence.c','restart-terminal-iapp.c')")
source=source.replace("flags=['gcc',", "flags=['gcc','-DWR_IOT_IAPP_POLICY_H','-DWR_IOT_IAPP_POLICY_PREPARED=1',",1)
source=source.replace("'physical-stop-session.c','radio-stop-fence.c']", "'physical-stop-session.c','radio-stop-fence.c','restart-wan-followup.c','restart-terminal-iapp.c','restart-iapp-child.c','restart-resume-retire.c']",1)
a='  f.write_text(content);compile_units.append(str(f))'
assert a in source
source=source.replace(a,r"""
  if n=='restart-iapp-child.c':
   import json,shlex
   script=p/'iapp-test.sh';event=p/'iapp-events'
   script.write_text('#!/bin/sh\nprintf \'%s\\n\' "$1" >> '+shlex.quote(str(event))+'\nexit 0\n');script.chmod(0o700)
   content=content.replace('"/usr/bin/iappd.sh"',json.dumps(str(script)))
  f.write_text(content);compile_units.append(str(f))
""",1)
a="print('PASS actual resume and Guest"
assert a in source
source=source.replace(a,"print('PASS enabled WAN/IAPP actual SDK planner/pump/terminal/child and resume/Guest",1)
a=" subprocess.run([d+'/check',d],check=True,timeout=30,env=env)"
assert a in source
# Append final one-script assertion after the entire per-case loop, before the with block ends.
marker="print('PASS enabled WAN/IAPP"
i=source.index(marker)
source=source[:i]+" subprocess.run([d+'/check',d],check=True,timeout=30,env={**os.environ,'WR_PHYSICAL_RESUME_TEST':'finish_pending'})\n assert (p/'iapp-events').read_text().splitlines()==['restart','restart']\n"+source[i:]
'''
text=text.replace(anchor,staging+'\n'+anchor,1)
exec(compile(text,__file__,'exec'),{'__file__':__file__})
