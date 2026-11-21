from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-radio-off-iapp.py').read_text();ns={'__file__':str(here/'check-radio-off-iapp.py')}
exec(compile(source[:source.rindex('with tempfile.TemporaryDirectory(')],'<OFF IAPP fixture>','exec'),ns)
body=ns['body']
body=body.replace(' for(int failure=0;failure<2;failure++){',r'''
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 struct wr_iot_saved_config config={.profile={.enabled=0,.ssid="IoT-B",.password="password-B",
  .gateway="192.168.50.1",.mask="255.255.255.0",.first="192.168.50.10",.last="192.168.50.30"}};
 assert(wr_iot_saved_config_encode(capture_record,sizeof(capture_record),&config));
#endif
 for(int failure=0;failure<2;failure++){''')

a='int main(int argc,char**argv){'
assert body.count(a)==1
body=body.replace(a,r'''
static int fail_restore;
static int injected_mask(int op,const sigset_t*set,sigset_t*old){if(op==SIG_SETMASK&&fail_restore)return -1;return sigprocmask(op,set,old);}
#define sigprocmask injected_mask
#include "radio-stop-fence.c"
#undef sigprocmask
static struct wr_iot_off_followup *finishing;
static struct wr_iot_radio_off_owner *finished_off;
static volatile sig_atomic_t shutdowns;
static void shutdown_handler(int sig){
 if(!wr_iot_rc_shutdown_note(sig)){
  assert(!depth&&!wr_iot_rc_shutdown.radio_off_owned&&finishing->phase==WR_OFF_FOLLOWUP_DONE);
  assert(!finishing->profile.baseline.active&&!finishing->profile.baseline.files.count&&!finishing->off&&!finishing->finish_off&&!finishing->finish_guard);
  assert(!finished_off->owner&&!finished_off->id[0]);shutdowns++;
 }
}
'''+a)
a='  /* Fixture-only free of retained RAM after checking non-retirement. */'
# Actual inherited fixture uses a different cleanup comment.
idx=body.index('  wr_iot_bundle_release(&s.profile.baseline.files);')
body=body[:idx]+r'''
  if(!failure){
   finishing=&s;finished_off=&off;struct sigaction sa={0};sa.sa_handler=shutdown_handler;sigemptyset(&sa.sa_mask);assert(!sigaction(SIGTERM,&sa,NULL));
   fail_restore=1;assert(!wr_iot_off_followup_finish(&s,&off));
   assert(s.phase==WR_OFF_FOLLOWUP_FINALIZING&&s.finish_guard==1&&s.profile.baseline.active&&depth==1&&wr_iot_rc_shutdown.radio_off_owned);
   assert(!kill(getpid(),SIGTERM)&&!shutdowns);
   fail_restore=0;assert(wr_iot_off_followup_finish(&s,&off));
   assert(shutdowns==1&&s.phase==WR_OFF_FOLLOWUP_DONE&&!depth&&!s.finish_fence.owner);
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
   assert(s.profile_receipt.valid&&s.profile_receipt.owner==getpid()&&!s.profile.self);
   assert(wr_iot_restart_profile_receipt_current(&s.profile_receipt));
#endif
   assert(!wr_iot_off_followup_finish(&s,&off));
   off=(struct wr_iot_radio_off_owner){.owner=getpid(),.result=1,.policy_ready=1,.policy={.reload=1},.released={WR_STOP_RELEASE,1,2,3,4,5,{1}}};
  }
'''+body[idx:]
with tempfile.TemporaryDirectory(prefix='wr-off-finish-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'check.c';p.write_text(body);b=root/'check'
 for prepared in (0,1):
  subprocess.run(['gcc','-DWR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED='+str(prepared),'-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
  subprocess.run([str(b),d],check=True,timeout=15)
print('PASS OFF final cleanup actual signal fence: failed mask restore retains baseline/guard/exclusion, same fence retry wipes/releases before real SIGTERM, one completion; SDK/terminal actors injected')
