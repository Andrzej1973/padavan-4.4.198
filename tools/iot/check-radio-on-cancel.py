"""Actual root cancellation, profile/RAM rollback and deferred signal replay."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-radio-on-owner.py').read_text();ns={'__file__':str(here/'check-radio-on-owner.py')}
exec(source.rsplit('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body'].split('int main(int argc',1)[0]+r'''
static int cancel_signals;
static void cancelled_signal(int sig){
 if(wr_iot_rc_shutdown_note(sig))return;
 assert(!on_owner.owner&&!wr_iot_radio_on_pending()&&!depth&&!wr_iot_rc_shutdown.active);
 assert(!wr_iot_rc_shutdown.radio_off_owned&&!wr_iot_rc_shutdown.radio_on_owned&&radio_off_receipt_valid);
 cancel_signals++;
}
int main(int argc,char**argv){
 (void)check;(void)shutdown_handler;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 strcpy(desired.gateway,"192.168.50.1");strcpy(desired.mask,"255.255.255.0");strcpy(desired.first,"192.168.50.20");strcpy(desired.last,"192.168.50.200");
 for(int after_generation=0;after_generation<2;after_generation++){
  receipt=(struct wr_iot_physical_stop_request){WR_STOP_RELEASE,1,2,3,4,5,{1}};radio_off_receipt_valid=1;
  down=1;partial=identity_fault=0;ups=generator_calls=rollback_calls=0;make_profile();
  FILE*f=fopen(profile_path,"a");assert(f&&fputs("# original baseline\n",f)>=0&&!fclose(f));
  struct wr_iot_control_request r={.id="01000000000000000000000000000000",.created=10,.request=desired};
  assert(wr_iot_rc_radio_on_begin(&r,1)&&!wr_iot_radio_on_step());
  if(after_generation)assert(!wr_iot_radio_on_step()&&generator_calls==1);
  struct sigaction sa={0};sa.sa_handler=cancelled_signal;sigemptyset(&sa.sa_mask);assert(!sigaction(SIGTERM,&sa,NULL));
  assert(!raise(SIGTERM));fail_unmask=1;
  int prior=cancel_signals;
  assert(!wr_iot_radio_on_step()&&on_owner.owner&&on_owner.admission.profile.active&&rollback_calls==1&&!ups&&cancel_signals==prior);
  fail_unmask=0;
  assert(wr_iot_radio_on_step()==-1&&cancel_signals==prior+1&&!on_owner.owner&&!depth&&radio_off_receipt_valid);
  assert(generator_calls==after_generation&&rollback_calls==1&&!ups&&!wr_iot_radio_on_pending());
  char bytes[4096];f=fopen(profile_path,"r");assert(f);size_t n=fread(bytes,1,sizeof(bytes)-1,f);bytes[n]=0;
  assert(!fclose(f)&&strstr(bytes,"# original baseline\n")&&!unlink(profile_path));
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-on-cancel-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'check.c';p.write_text('#define WR_IOT_IAPP_POLICY_H\n#define WR_IOT_IAPP_POLICY_PREPARED 1\n'+body);b=root/'check'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b),d],check=True,timeout=15)
print('PASS actual ON root pre-UP cancellation: before/after generation baseline restored, RAM once, failed mask retains owner, retry clears buffers/exclusions before real SIGTERM, OFF receipt preserved, zero Main UP; SDK/backend actors')
