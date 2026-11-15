"""Actual root pre-UP failure without shutdown; baseline and exclusion lifetime."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-radio-on-owner.py').read_text();ns={'__file__':str(here/'check-radio-on-owner.py')}
exec(source.rsplit('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body'].split('int main(int argc',1)[0]+r'''
int main(int argc,char**argv){
 (void)check;(void)shutdown_handler;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 strcpy(desired.gateway,"192.168.50.1");strcpy(desired.mask,"255.255.255.0");strcpy(desired.first,"192.168.50.20");strcpy(desired.last,"192.168.50.200");
 for(int fault=0;fault<3;fault++){
  receipt=(struct wr_iot_physical_stop_request){WR_STOP_RELEASE,1,2,3,4,5,{1}};radio_off_receipt_valid=1;
  down=1;partial=fault==1?2:1;identity_fault=0;ups=generator_calls=rollback_calls=0;make_profile();
  FILE*f=fopen(profile_path,"a");assert(f&&fputs("# baseline failure recovery\n",f)>=0&&!fclose(f));
  struct wr_iot_control_request input={.id="01000000000000000000000000000000",.created=10,.request=desired};
  assert(wr_iot_rc_radio_on_begin(&input,1));assert(!wr_iot_radio_on_step());
  assert(!wr_iot_radio_on_step()&&generator_calls==1&&!ups);
  if(fault==2){
   char path[1100];snprintf(path,sizeof(path),"%s/foreign",argv[1]);f=fopen(path,"w");assert(f&&fputs("foreign\n",f)>=0&&!fclose(f)&&!rename(path,profile_path));
  }
  int result=0;for(int tick=0;tick<8&&!result;tick++)result=wr_iot_radio_on_step();
  if(fault<2){
   assert(result==-1&&!on_owner.owner&&!depth&&!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.radio_on_owned&&radio_off_receipt_valid&&rollback_calls==1);
   char bytes[4096];f=fopen(profile_path,"r");assert(f);size_t n=fread(bytes,1,sizeof(bytes)-1,f);bytes[n]=0;assert(!fclose(f)&&strstr(bytes,"# baseline failure recovery\n"));
  }else{
   assert(!result&&on_owner.owner&&on_owner.admission.profile.active&&depth==1&&wr_iot_rc_shutdown.radio_on_owned&&!rollback_calls);
   char bytes[64];f=fopen(profile_path,"r");assert(f&&fgets(bytes,sizeof(bytes),f)&&!fclose(f)&&!strcmp(bytes,"foreign\n"));
   /* Fixture-only disposal of intentionally retained foreign generation. */
   wr_iot_bundle_release(&on_owner.admission.profile.files);memset(&on_owner.admission.profile,0,sizeof(on_owner.admission.profile));on_owner.admission.busy=0;
   assert(wr_iot_on_admission_cancel(&on_owner.admission));on_owner_wipe(&on_owner,sizeof(on_owner));wr_iot_rc_shutdown.radio_on_owned=0;
  }
  assert(generator_calls==1&&!ups&&!wr_iot_rc_shutdown.pending&&!unlink(profile_path));
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-on-failure-recover-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'check.c';p.write_text('#define WR_IOT_IAPP_POLICY_H\n#define WR_IOT_IAPP_POLICY_PREPARED 1\n'+body);b=root/'check'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b),d],check=True,timeout=15)
print('PASS ON actual root non-shutdown failure: partial/invalid generation restores original bytes, RAM OFF once and cancelled root cleanup, old OFF receipt retained, foreign inode holds/no overwrite/no replay, zero Main UP; SDK actors')
