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
 make_profile();radio_off_receipt_valid=1;down=1;
 struct wr_iot_control_request r={.id="01000000000000000000000000000000",.created=10,.request=desired};
 assert(wr_iot_rc_radio_on_begin(&r,1));down=0;
 assert(!wr_iot_radio_on_step()&&on_owner.phase==ON_OWNER_RETAINED&&!on_owner.restore.generation.owner&&!generator_calls&&!ups);
 down=1;
 for(int tick=0;tick<4;tick++)assert(!wr_iot_radio_on_step());
 assert(on_owner.owner&&depth==1&&wr_iot_rc_shutdown.active&&on_owner.restore.owner&&!on_owner.restore.generation.owner&&!on_owner.admission.busy);
 /* Confirm the retained admission remains capture-only, never generated. */
 assert(!on_owner.admission.profile.generated&&!on_owner.admission.profile.files.journalled&&!ram_calls&&!ups&&!generator_calls);
 assert(wr_iot_on_admission_cancel(&on_owner.admission));on_owner_wipe(&on_owner,sizeof(on_owner));wr_iot_rc_shutdown.radio_on_owned=0;
 assert(!unlink(profile_path));
}
'''
with tempfile.TemporaryDirectory(prefix='wr-on-failure-recover-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'check.c';p.write_text('#define WR_IOT_IAPP_POLICY_H\n#define WR_IOT_IAPP_POLICY_PREPARED 1\n'+body);b=root/'check'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b),d],check=True,timeout=15)
print('CONFIRMED capture-only begin refusal retains root after DOWN proof returns; no generation/RAM/UP; recovery gap, not a passing completion gate')
