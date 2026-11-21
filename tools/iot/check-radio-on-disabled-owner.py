"""Actual stable root owns disabled IoT restoration and terminal retirement."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-radio-on-owner.py')}
exec((here/'check-radio-on-owner.py').read_text().rsplit('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body'].split('int main(int argc',1)[0]+r'''
int main(int argc,char**argv){
 (void)check;(void)shutdown_handler;assert(argc==2);snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 make_profile();membership=guest_desired=guest_isolate=1;mc_read=aux_ok=1;up_result=WR_RESTART_UP_RETURNED;
 struct wr_iot_control_request r={.id="01000000000000000000000000000000",.created=10};
 struct wr_iot_control_request wrong=r;strcpy(wrong.request.ssid,"not-an-off-intent");assert(!wr_iot_rc_radio_on_begin(&wrong,1));
 assert(wr_iot_rc_radio_on_begin(&r,1));
 int done=0,release_seen=0;
 for(int tick=0;tick<60&&!done;tick++){
  done=wr_iot_radio_on_step();
  if(on_owner.restore.phase==WR_ON_RESTORE_RELEASED){release_seen=1;assert(wr_iot_rc_shutdown.radio_on_owned&&!depth&&!radio_off_receipt_valid);}
 }
 assert(done==1&&release_seen&&ups==1&&generator_calls==1&&wan_submits==1&&led_calls==1&&child_begins==1&&!begins);
 network_current=0;assert(!wr_iot_radio_on_retire()&&on_owner.owner);network_current=1;
 assert(wr_iot_radio_on_retire()&&!on_owner.owner&&!wr_iot_radio_on_pending()&&!wr_iot_rc_shutdown.radio_on_owned);
 assert(!unlink(profile_path));
}
'''
with tempfile.TemporaryDirectory(prefix='wr-on-owner-') as d:
    root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
    p=root/'check.c';p.write_text('#define WR_IOT_IAPP_POLICY_H\n#define WR_IOT_IAPP_POLICY_PREPARED 1\n'+body);b=root/'check'
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
    subprocess.run([str(b),d],check=True,timeout=15)
print('PASS actual disabled stable root: no credential-bearing OFF intent, one generation/Main/WAN/LED/IAPP, exclusion survives release, no rebind OPEN, stale idle blocks retirement, fresh DONE wipes root; SDK actors')
