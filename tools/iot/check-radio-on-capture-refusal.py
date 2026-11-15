"""Capture-only refused ON owner: exact readback cleanup, no generation retry."""
from pathlib import Path
import subprocess,tempfile,sys
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-radio-on-owner.py')}
exec((here/'check-radio-on-owner.py').read_text().rsplit('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body'].split('int main(int argc',1)[0]
a='int wr_iot_rc_radio_on_rollback_current(const struct wr_iot_physical_stop_request*r){assert(depth&&r->action==WR_STOP_RELEASE);return down&&rollback_calls>0;}'
assert body.count(a)==1
body=body.replace(a,'static int ram_off=1;\nint wr_iot_rc_radio_on_rollback_current(const struct wr_iot_physical_stop_request*r){assert(depth&&r->action==WR_STOP_RELEASE);return down&&ram_off;}')
if len(sys.argv)==2:
 body=body.replace('#include "radio-on-owner.c"','#include "'+str(Path(sys.argv[1]).resolve())+'"')
body+=r'''
static int captured_signals;
static void captured_signal(int sig){
 if(wr_iot_rc_shutdown_note(sig))return;
 assert(!on_owner.owner&&!depth&&!wr_iot_rc_shutdown.active&&radio_off_receipt_valid);
 assert(!wr_iot_rc_shutdown.radio_on_owned&&!wr_iot_rc_shutdown.radio_off_owned);
 captured_signals++;
}
int main(int argc,char**argv){
 (void)check;(void)shutdown_handler;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 strcpy(desired.gateway,"192.168.50.1");strcpy(desired.mask,"255.255.255.0");strcpy(desired.first,"192.168.50.20");strcpy(desired.last,"192.168.50.200");
 struct sigaction sa={0};sa.sa_handler=captured_signal;sigemptyset(&sa.sa_mask);assert(!sigaction(SIGTERM,&sa,NULL));
 for(int fault=0;fault<5;fault++){
  make_profile();radio_off_receipt_valid=1;down=ram_off=1;fail_unmask=0;
  struct wr_iot_control_request r={.id="01000000000000000000000000000000",.created=10,.request=desired};
  assert(wr_iot_rc_radio_on_begin(&r,1));down=0;
  assert(!wr_iot_radio_on_step()&&on_owner.phase==ON_OWNER_RETAINED&&!on_owner.restore.generation.owner);
  assert(!wr_iot_radio_on_step()&&on_owner.owner&&depth==1);
  down=1;
  if(fault==1)ram_off=0;
  if(fault==2){FILE*f=fopen(profile_path,"a");assert(f&&fputs("# foreign mutation\n",f)>=0&&!fclose(f));}
  if(fault==3)fail_unmask=1;
  if(fault==4)assert(!kill(getpid(),SIGTERM));
  int result=wr_iot_radio_on_step();
  if(!fault||fault==4)assert(result==-1&&!on_owner.owner&&!depth&&!wr_iot_rc_shutdown.active);
  else{
   assert(!result&&on_owner.owner&&depth==1&&wr_iot_rc_shutdown.active);
   if(fault==1||fault==3){ram_off=1;fail_unmask=0;assert(wr_iot_radio_on_step()==-1&&!on_owner.owner&&!depth);}
   else{wr_iot_bundle_release(&on_owner.admission.profile.files);memset(&on_owner.admission.profile,0,sizeof(on_owner.admission.profile));assert(wr_iot_on_admission_cancel(&on_owner.admission));on_owner_wipe(&on_owner,sizeof(on_owner));wr_iot_rc_shutdown.radio_on_owned=0;}
  }
  if(fault==4)assert(captured_signals==1);
  assert(radio_off_receipt_valid&&!generator_calls&&!ram_calls&&!rollback_calls&&!ups&&!unlink(profile_path));
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-on-capture-refusal-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'check.c';p.write_text('#define WR_IOT_IAPP_POLICY_H\n#define WR_IOT_IAPP_POLICY_PREPARED 1\n'+body);b=root/'check'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b),d],check=True,timeout=15)
print('PASS capture-only refusal: stale DOWN/RAM/profile and failed unmask retain; fresh proof cleanup preserves OFF receipt; zero generator/RAM-write/Main UP; SDK actors')
