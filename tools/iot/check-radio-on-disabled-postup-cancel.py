"""Actual root post-UP shutdown cleanup, retained mask fault and real signal."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-radio-on-owner.py').read_text();ns={'__file__':str(here/'check-radio-on-owner.py')}
exec(source.rsplit('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body'].split('int main(int argc',1)[0]+r'''
static int stopped;
static void postop_signal(int sig){
 if(wr_iot_rc_shutdown_note(sig))return;
 assert(!on_owner.owner&&!wr_iot_radio_on_pending()&&!depth&&!radio_off_receipt_valid);
 assert(!wr_iot_rc_shutdown.radio_off_owned&&!wr_iot_rc_shutdown.radio_on_owned&&!wr_iot_rc_shutdown.active);
 stopped++;
}
int main(int argc,char**argv){
 (void)check;(void)shutdown_handler;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 strcpy(desired.gateway,"192.168.50.1");strcpy(desired.mask,"255.255.255.0");strcpy(desired.first,"192.168.50.20");strcpy(desired.last,"192.168.50.200");
 for(int boundary=0;boundary<3;boundary++){
  receipt=(struct wr_iot_physical_stop_request){WR_STOP_RELEASE,1,2,3,4,5,{1}};radio_off_receipt_valid=1;
  down=1;partial=identity_fault=0;ups=generator_calls=rollback_calls=attaches=0;membership=1;make_profile();
  guest_desired=guest_isolate=1;guest_state=guest_bridge=guest_isolated=guest_adds=guest_ups=guest_downs=0;
  bridge_fail=no_submit=ram_fail=mc_fail=0;ram_calls=mc_calls=service_calls=0;mc_read=aux_ok=1;up_result=WR_RESTART_UP_RETURNED;
  struct wr_iot_control_request r={.id="01000000000000000000000000000000",.created=10};
  assert(wr_iot_rc_radio_on_begin(&r,1));
  for(int tick=0;tick<40;tick++){
   assert(!wr_iot_radio_on_step());
   if(boundary==2?on_owner.phase==ON_OWNER_RELEASE:
      boundary==1?on_owner.phase==ON_OWNER_HANDOFF:on_owner.restore.phase==WR_ON_RESTORE_MAIN_WAIT)break;
  }
  assert(ups==1&&!on_owner.restore.handoff_created&&on_owner.admission.profile.active);
  if(boundary==2){fail_unmask=1;assert(!wr_iot_radio_on_step()&&radio_on_releasing==&on_owner.restore&&on_owner.restore.wan.owner==getpid());}
  struct sigaction sa={0};sa.sa_handler=postop_signal;sigemptyset(&sa.sa_mask);assert(!sigaction(SIGTERM,&sa,NULL));
  assert(!raise(SIGTERM));fail_unmask=1;int prior=stopped;
  assert(!wr_iot_radio_on_step()&&on_owner.owner&&on_owner.admission.profile.active&&radio_off_receipt_valid&&stopped==prior);
  assert(rc_on_shutdown.restore==&on_owner.restore&&depth==1&&ups==1&&!rollback_calls);
  fail_unmask=0;idle_delivery=0;
  assert(!wr_iot_radio_on_step()&&on_owner.owner&&radio_off_receipt_valid&&stopped==prior);
  idle_delivery=1;identity_fault=1;
  assert(!wr_iot_radio_on_step()&&on_owner.owner&&radio_off_receipt_valid&&stopped==prior);
  identity_fault=0;assert(wr_iot_radio_on_step()==-1&&stopped==prior+1&&!on_owner.owner&&!depth&&!radio_off_receipt_valid);
  assert(ups==1&&generator_calls==1&&!rollback_calls&&!wr_iot_radio_on_pending());
  /* CURRENT generated profile preserved; physical shutdown belongs to stock handler. */
  int fd=open(profile_path,O_RDONLY);assert(fd>=0&&!close(fd)&&!unlink(profile_path));
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-on-postup-cancel-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'check.c';p.write_text('#define WR_IOT_IAPP_POLICY_H\n#define WR_IOT_IAPP_POLICY_PREPARED 1\n'+body);b=root/'check'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b),d],check=True,timeout=15)
print('PASS actual disabled post-UP root shutdown with fresh double idle: Main-WAIT/PREPARED, Guest drain, mask failure retains baseline/receipt, retry wipes root/old receipt before real SIGTERM, no profile rollback/second UP/RAM rollback; SDK/stock shutdown actor, not physical retirement')
