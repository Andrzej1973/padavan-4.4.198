#!/usr/bin/env python3
"""Actual ON owner with absent/configured native desired records, host only."""
from pathlib import Path
import ast,subprocess,tempfile
here=Path(__file__).resolve().parent
text=(here/'check-radio-on-owner.py').read_text()
ns={'__file__':str(here/'check-radio-on-owner.py')}
exec(compile(text[:text.index('\nwith tempfile.TemporaryDirectory(')],'<on-owner>','exec'),ns)
tree=ast.parse((here/'check-cold-config-revision.py').read_text())
provider=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='provider' for t in n.targets))
provider=provider.replace('#include "saved-config-store.c"','#define admitted wr_saved_fixture_admitted\n#include "saved-config-store.c"\n#undef admitted')
body=ns['body'];anchor='#include "radio-on-generation.c"';assert body.count(anchor)==1
body=body.replace(anchor,provider+'\n'+anchor)
# RC receipt storage is outside this isolated owner fixture. All entries use
# reload1; its historical file observer must stay unused. Rollback receipt
# publication is a validated injected boundary, exercised in RC composition.
body=body.replace('#include "radio-on-release-runtime.h"',r'''
static struct wr_iot_restart_profile_receipt radio_off_profile_receipt;
int wr_iot_rc_radio_off_profile_current(const struct wr_iot_physical_stop_request *r){(void)r;assert(0);return 0;}
int wr_iot_rc_radio_on_rollback_receipt(const struct wr_iot_on_generation *g){
 assert(depth==1&&g&&g->owner==getpid()&&!g->busy&&!g->main_may_have_started&&
  g->phase==WR_ON_GEN_RESTORED&&g->admission&&g->admission->profile.recovered);
 return 1;
}
#include "radio-on-release-runtime.h"
''')
configured=body
anchor='struct wr_iot_control_request r={.id="01000000000000000000000000000000",.created=10,.request=desired},wrong=r;'
assert configured.count(anchor)==1
configured=configured.replace(anchor,r'''struct wr_iot_saved_config next={.profile=desired};
 record_present=1;record_error=0;
 assert(wr_iot_saved_config_encode(desired_record,sizeof(desired_record),&next));
 strcpy(saved_ssid,"IoT"); /* Legacy stays old. */
'''+anchor,1)
configured=configured.replace('static void make_saved_profile(void){',r'''#include "generation-profile.h"
static void make_saved_profile(void){
 struct wr_iot_precreated_profile_request captured={0};
 assert(wr_iot_generation_profile_request(&captured)==1);
''',1)
configured=configured.replace('wr_iot_precreated_profile(in,out,saved_ssid,saved_password,0)',
 'wr_iot_precreated_profile(in,out,captured.ssid,captured.password,0)',1)
configured=configured.replace('assert(done&&saw_release&&ups==1&&wan_submits==1&&child_begins==1&&begins==1);',
 'assert(done&&saw_release&&ups==1&&wan_submits==1&&child_begins==1&&begins==1);\n {struct wr_iot_generation_config empty={0};struct wr_iot_saved_config clear={0};\n assert(!memcmp(&on_owner.restore.generation.config_revision,&empty,sizeof(empty)));\n assert(!memcmp(&on_owner.restore.generation.provisioning,&clear,sizeof(clear)));}')

with tempfile.TemporaryDirectory(prefix='wr-on-owner-desired-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\nint nvram_getall(char *,int,int);\nint nvram_set(const char *,const char *);\n')
 (root/'wr-band-settings-snapshot.h').write_bytes((here.parent/'band-steering/settings-snapshot.h').read_bytes())
 for mode,unit in [('absent',body),('configured',configured)]:
  (root/'check.c').write_text('#define WR_IOT_IAPP_POLICY_H\n#define WR_IOT_IAPP_POLICY_PREPARED 1\n'+unit)
  subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-DWR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED=1','-DWR_IOT_NATIVE_NVRAM_SPACE=61440','-DWR_IOT_NATIVE_NVRAM_HEADER_BYTES=20','-I'+d,'-I'+str(here),str(root/'check.c'),str(here.parent/'band-steering/settings-snapshot.c'),'-o',str(root/'check')],check=True)
  subprocess.run([str(root/'check'),d],check=True,timeout=15)
  print('PASS actual ON desired owner mode:',mode,flush=True)
print('PASS actual ON owner/mode/native capture/generation/release/WAN/terminal with absent and configured records while legacy SSID stays old; SDK/backend actors, no device acceptance')
