"""Private stable ON root with actual release/child composition and mode reader."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-radio-on-followup.py').read_text()
ns={'__file__':str(here/'check-radio-on-followup.py')}
exec(source.rsplit('for gate in (0,1):',1)[0],ns)
body=ns['body'].split('int main(int argc',1)[0]
anchor='int wr_iot_rc_radio_on_mode_read(struct wr_iot_rc_mode *m){m->router=m->radio=1;m->mode=0;return 1;}'
assert body.count(anchor)==1
body=body.replace(anchor,'int get_ap_mode(void){return 0;}\nint get_enabled_radio_rt(void){return 1;}\nint get_mode_radio_rt(void){return 0;}\nint is_radio_on_rt(void){return !down;}\n#include "rc-mode.c"')
body=body.replace('!strcmp(r->request.ssid,"IoT")','!strcmp(r->request.ssid,desired.ssid)')
body=body.replace('int wr_iot_rc_restart_generate(int arg)',r'''
static void make_saved_profile(void){
 FILE *in=tmpfile(),*out=fopen(profile_path,"w");assert(in&&out);assert(fputs(baseline,in)>=0);rewind(in);
 assert(wr_iot_precreated_profile(in,out,saved_ssid,saved_password,0));assert(!fclose(in)&&!fclose(out));
}
int wr_iot_rc_restart_generate(int arg)''').replace('make_profile();return 0;}', 'make_saved_profile();return 0;}')
body+=r'''
#include "radio-on-owner.c"
int main(int argc,char**argv){
 (void)check;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 strcpy(desired.gateway,"192.168.50.1");strcpy(desired.mask,"255.255.255.0");strcpy(desired.first,"192.168.50.20");strcpy(desired.last,"192.168.50.200");
 for(int fault=0;fault<3;fault++){
  receipt=(struct wr_iot_physical_stop_request){WR_STOP_RELEASE,1,2,3,4,5,{1}};radio_off_receipt_valid=1;
  down=1;partial=identity_fault=0;ups=generator_calls=attaches=0;membership=1;strcpy(saved_ssid,"IoT");strcpy(desired.ssid,"IoT");make_profile();
  if(!fault){strcpy(saved_ssid,"IoT-new");strcpy(desired.ssid,"IoT-new");}
  guest_desired=guest_isolate=1;guest_state=guest_bridge=guest_isolated=guest_adds=guest_ups=guest_downs=0;bridge_fail=no_submit=0;
  ram_calls=mc_calls=service_calls=0;ram_fail=fault==2;mc_fail=0;mc_read=aux_ok=1;up_result=WR_RESTART_UP_RETURNED;
  auth_current=wan_current=1;wan_submits=led_calls=child_begins=child_steps=0;network_current=1;child_failure=fault==1;child_unknown=0;
  admitted=active=1;begins=continues=0;
  releasing=&on_owner.restore;released_admission=&on_owner.admission;
  struct sigaction sa={0};sa.sa_handler=shutdown_handler;sigemptyset(&sa.sa_mask);assert(!sigaction(SIGTERM,&sa,NULL));
  struct wr_iot_control_request r={.id="01000000000000000000000000000000",.created=10,.request=desired},wrong=r;
  strcpy(wrong.request.last,"192.168.99.200");assert(!wr_iot_rc_radio_on_begin(&wrong,1)&&!wr_iot_radio_on_pending());
  wrong=r;memset(wrong.id,'0',32);assert(!wr_iot_rc_radio_on_begin(&wrong,1)&&!wr_iot_radio_on_pending());
  assert(wr_iot_rc_radio_on_begin(&r,1)&&wr_iot_radio_on_pending()&&wr_iot_rc_shutdown.radio_on_owned);
  assert(!wr_iot_rc_radio_on_begin(&r,1)&&!wr_iot_radio_on_retire());
  assert(!wr_iot_radio_on_step()&&!on_owner.input.request.password[0]);
  int done=0,saw_release=0;
  for(int tick=0;tick<50&&!done;tick++){
   done=wr_iot_radio_on_step();
   if(on_owner.restore.phase==WR_ON_RESTORE_RELEASED){saw_release=1;assert(wr_iot_rc_shutdown.radio_on_owned&&!wr_iot_rc_shutdown.radio_off_owned&&!wr_iot_rc_shutdown.active&&!depth);}
   assert(wr_iot_rc_shutdown.radio_on_owned);
  }
  if(fault){
   assert(!done&&on_owner.phase==ON_OWNER_RETAINED&&wr_iot_radio_on_pending()&&!wr_iot_radio_on_retire());
   assert(fault==1?(saw_release&&ups==1&&child_begins==1):(!ups&&!wan_submits&&on_owner.admission.profile.active));
   /* Fixture-only retained-state teardown; production failure cleanup unfinished. */
   wr_iot_bundle_release(&on_owner.admission.profile.files);memset(&on_owner.admission.profile,0,sizeof(on_owner.admission.profile));
   if(on_owner.admission.guard){on_owner.admission.busy=0;assert(wr_iot_on_admission_cancel(&on_owner.admission));}
   on_owner_wipe(&on_owner,sizeof(on_owner));wr_iot_rc_shutdown.radio_on_owned=0;
  }else{
   assert(done&&saw_release&&ups==1&&wan_submits==1&&child_begins==1&&begins==1);
   network_current=0;assert(!wr_iot_radio_on_retire()&&wr_iot_radio_on_pending());network_current=1;
   assert(wr_iot_radio_on_retire()&&!wr_iot_radio_on_pending()&&!wr_iot_rc_shutdown.radio_on_owned&&!on_owner.owner);
   assert(!wr_iot_radio_on_retire()&&!wr_iot_rc_radio_on_begin(&r,1)); /* consumed OFF receipt */
  }
  assert(!depth&&!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.radio_off_owned);
  assert(!unlink(profile_path));
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-on-owner-') as d:
    root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
    p=root/'check.c';p.write_text('#define WR_IOT_IAPP_POLICY_H\n#define WR_IOT_IAPP_POLICY_PREPARED 1\n'+body);b=root/'check'
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
    subprocess.run([str(b),d],check=True,timeout=15)
print('PASS stable ON root actual mode/profile/release/WAN/terminal chain: validation, credentials dropped after capture, one begin/UP/WAN/child, ON exclusion survives parent release, fresh DONE retirement, failure retained not reusable; SDK/backend actors, no public entry/runtime acceptance')
