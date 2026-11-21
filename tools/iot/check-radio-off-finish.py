from pathlib import Path
import argparse,resource,signal,subprocess,tempfile
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
static int publish_ready=1,prepare_calls,publish_calls;
static int prepare_publication(const struct wr_iot_off_followup*s,void*context){
 assert(context==&publish_calls&&depth==1&&s==finishing&&s->phase==WR_OFF_FOLLOWUP_FINALIZING&&s->finish_guard==1&&wr_iot_rc_shutdown.active&&wr_iot_rc_shutdown.radio_off_owned);
 prepare_calls++;return publish_ready;
}
static void publish_completion(const struct wr_iot_off_followup*s,void*context){
 assert(context==&publish_calls&&depth==1&&s==finishing&&s->phase==WR_OFF_FOLLOWUP_DONE&&s->finish_guard==1&&s->finish_fence.owner==getpid());
 assert(!s->profile.baseline.active&&!finished_off->owner&&!wr_iot_rc_shutdown.radio_off_owned);
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 assert(wr_iot_restart_profile_receipt_current(&s->profile_receipt));
#endif
 publish_calls++;
}
static volatile sig_atomic_t shutdowns,routed_replays;
static void shutdown_handler(int sig){
 if(wr_iot_rc_shutdown.normal_route_requested&&!wr_iot_rc_shutdown.active){
  assert(publish_calls==1&&finishing->finish_published&&finishing->phase==WR_OFF_FOLLOWUP_DONE&&!depth);routed_replays++;
 }
 if(!wr_iot_rc_shutdown_note(sig)){
  assert(!depth&&!wr_iot_rc_shutdown.radio_off_owned&&finishing->phase==WR_OFF_FOLLOWUP_DONE);
  assert(!finishing->profile.baseline.active&&!finishing->profile.baseline.files.count&&!finishing->off&&!finishing->finish_off&&!finishing->finish_guard);
  assert(!finished_off->owner&&!finished_off->id[0]&&publish_calls==1&&finishing->finish_published);shutdowns++;
 }
}
'''+a)
a='  /* Fixture-only free of retained RAM after checking non-retirement. */'
# Actual inherited fixture uses a different cleanup comment.
idx=body.index('  wr_iot_bundle_release(&s.profile.baseline.files);')
body=body[:idx]+r'''
  if(!failure){
   finishing=&s;finished_off=&off;struct sigaction sa={0};sa.sa_handler=shutdown_handler;sigemptyset(&sa.sa_mask);assert(!sigaction(SIGTERM,&sa,NULL));
   if(route_mode){wr_iot_rc_shutdown.normal_route_armed=1;wr_iot_rc_shutdown.normal_route_requested=SIGTERM;}
   assert(wr_iot_off_followup_bind_publisher(&s,prepare_publication,publish_completion,&publish_calls));
   assert(!wr_iot_off_followup_bind_publisher(&s,prepare_publication,publish_completion,NULL));
   publish_ready=0;assert(!wr_iot_off_followup_finish(&s,&off)&&!publish_calls);publish_ready=1;
   assert(s.phase==WR_OFF_FOLLOWUP_FINALIZING&&s.profile.baseline.active&&depth==1);
   fail_restore=1;assert(!wr_iot_off_followup_finish(&s,&off));
   observed=0;assert(!wr_iot_off_followup_finish(&s,&off)&&!publish_calls);observed=1;
   s.policy.stored_radio^=1;assert(!wr_iot_off_followup_finish(&s,&off));s.policy.stored_radio^=1;
   if(argc==3&&!route_mode){
    FILE*f=fopen(profile_path,"a");assert(f&&fputs("# external drift\n",f)>=0&&!fclose(f));
    fail_restore=0;assert(!wr_iot_off_followup_finish(&s,&off)&&!publish_calls);
    assert(s.phase==WR_OFF_FOLLOWUP_FINALIZING&&s.profile.baseline.active&&depth==1&&wr_iot_rc_shutdown.radio_off_owned);
    wr_iot_bundle_release(&s.profile.baseline.files);assert(!unlink(profile_path));return 0;
   }
   assert(s.phase==WR_OFF_FOLLOWUP_FINALIZING&&s.finish_guard==1&&s.profile.baseline.active&&depth==1&&wr_iot_rc_shutdown.radio_off_owned);
   assert(!kill(getpid(),SIGTERM)&&!shutdowns);
   fail_restore=0;assert(wr_iot_off_followup_finish(&s,&off));
   assert(shutdowns==!route_mode&&routed_replays==route_mode&&s.phase==WR_OFF_FOLLOWUP_DONE&&!depth&&!s.finish_fence.owner);
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
   assert(s.profile_receipt.valid&&s.profile_receipt.owner==getpid()&&!s.profile.self);
   assert(wr_iot_restart_profile_receipt_current(&s.profile_receipt));
#endif
   assert(!wr_iot_off_followup_finish(&s,&off));
   if(route_mode){assert(!unlink(profile_path));return 0;}
   off=(struct wr_iot_radio_off_owner){.owner=getpid(),.result=1,.policy_ready=1,.policy={.reload=1},.released={WR_STOP_RELEASE,1,2,3,4,5,{1}}};
  }
'''+body[idx:]
body=body.replace('assert(argc==2);','assert(argc==2||argc==3);int route_mode=argc==3&&argv[2][0]==\'r\';')
parser=argparse.ArgumentParser()
parser.add_argument('--target-compiler',type=Path)
parser.add_argument('--target-sysroot',type=Path)
parser.add_argument('--qemu',type=Path)
args=parser.parse_args()
if any((args.target_compiler,args.target_sysroot,args.qemu)) and not all((args.target_compiler,args.target_sysroot,args.qemu)):
 parser.error('target compiler, sysroot and QEMU must be supplied together')
with tempfile.TemporaryDirectory(prefix='wr-off-finish-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'check.c';p.write_text(body);b=root/'check'
 for prepared in (0,1):
  flags=['-mips32r2','-march=mips32r2','-mtune=1004kc'] if args.target_compiler else ['-fsanitize=address,undefined']
  subprocess.run([str(args.target_compiler) if args.target_compiler else 'gcc','-DWR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED='+str(prepared),'-std=gnu11','-Wall','-Wextra','-Werror','-O2',*flags,'-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
  run=[str(args.qemu),'-L',str(args.target_sysroot)] if args.target_compiler else []
  for extra in ([],['drift'],['route']):subprocess.run(run+[str(b),d]+extra,check=True,timeout=15)
 if not args.target_compiler:
  # Predecessor-equivalent omission must fail at the real file-drift retry,
  # with mask restoration enabled, rather than pass because the mask failed.
  source=(here/'radio-off-followup.c').read_text()
  anchor=' if(!wr_iot_off_followup_final_current(s)||\n    (!!s->finish_prepare'
  assert source.count(anchor)==1
  mutant=root/'off-mutant.c';mutant.write_text(source.replace(anchor,' if((0&&!wr_iot_off_followup_final_current(s))||\n    (!!s->finish_prepare',1))
  probe=body.replace('#include "radio-off-followup.c"','#include "'+str(mutant)+'"')
  probe=probe.replace('    fail_restore=0;assert(!wr_iot_off_followup_finish(&s,&off)&&!publish_calls);','    fputs("DRIFT_RETRY_BOUNDARY\\n",stderr);fail_restore=0;assert(!wr_iot_off_followup_finish(&s,&off)&&!publish_calls);')
  p.write_text(probe)
  subprocess.run(['gcc','-DWR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED=0','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
  def no_core():resource.setrlimit(resource.RLIMIT_CORE,(0,0))
  result=subprocess.run([str(b),d,'drift'],capture_output=True,text=True,timeout=15,preexec_fn=no_core)
  assert result.returncode==-signal.SIGABRT and 'DRIFT_RETRY_BOUNDARY' in result.stderr and '!publish_calls' in result.stderr,result.stderr
  print('PASS mutation: omitted retained final preflight fails at real file-drift retry with unmask enabled; core disabled')
print('PASS OFF finalizer prepared0/1: publisher refusal and real file drift retain baseline/guard; fresh retained retry, atomic publication before real TERM/routed replay, single commit; SDK/terminal actors injected')
