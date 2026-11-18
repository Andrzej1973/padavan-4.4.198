"""Actual initial generator selector + native store/snapshot/guard composition."""
from pathlib import Path
import ast
import subprocess
import tempfile
here=Path(__file__).resolve().parent
tree=ast.parse((here/'check-rc-desired-config.py').read_text())
body=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
          and any(isinstance(t,ast.Name) and t.id=='body' for t in n.targets))
body=body.split('int main(void){',1)[0]+r'''
static int legacy_calls,entropy_calls;
static const char *legacy(void *unused,const char *key){
 (void)unused;legacy_calls++;
 if(!strcmp(key,"wr_iot_enable"))return "0";
 if(!strcmp(key,"wr_iot_ssid"))return "Legacy preserved";
 assert(!strcmp(key,"wr_iot_psk"));return "legacy-password";
}
static int entropy(void *unused,unsigned char *bytes,unsigned int count){
 (void)unused;(void)bytes;(void)count;entropy_calls++;return -1;
}
static int select_profile(struct wr_iot_precreated_profile_request *out){
 return wr_iot_generation_boot_request_read(out,legacy,NULL,entropy,NULL);
}
int main(void){
 struct wr_iot_precreated_profile_request out,before;
 memset(&before,0x5a,sizeof(before));reset();wr_iot_rc_shutdown.active=0;
 for(int enabled=0;enabled<=1;enabled++){
  config.profile.enabled=enabled;present=1;
  assert(wr_iot_saved_config_encode(native_record,sizeof(native_record),&config));
  out=before;assert(select_profile(&out)&&out.provisioned==1&&out.requested_enabled==enabled);
  assert(!strcmp(out.ssid,config.profile.ssid)&&!strcmp(out.password,config.profile.password));
  assert(!legacy_calls&&!entropy_calls&&!writes&&wr_iot_service_guard_dup()<0);
 }
 read_error=1;out=before;assert(!select_profile(&out)&&!memcmp(&out,&before,sizeof(out)));
 read_error=0;strcpy(native_record,"malformed");
 assert(!select_profile(&out)&&!memcmp(&out,&before,sizeof(out))&&!legacy_calls);
 assert(wr_iot_saved_config_encode(native_record,sizeof(native_record),&config));
 snapshot_calls=0;change_on_read=1;
 assert(!select_profile(&out)&&!memcmp(&out,&before,sizeof(out))&&!legacy_calls);
 present=0;snapshot_calls=0;
 assert(!select_profile(&out)&&!memcmp(&out,&before,sizeof(out))&&!legacy_calls);
 change_on_read=0;present=0;
 assert(select_profile(&out)&&out.provisioned&&!strcmp(out.ssid,"Legacy preserved")&&legacy_calls);
 assert(!writes&&!entropy_calls&&wr_iot_service_guard_dup()<0);
 /* Nested generation borrows one guard depth and leaves its caller's intact. */
 assert(wr_iot_service_guard_enter(1)==1);present=1;
 assert(wr_iot_saved_config_encode(native_record,sizeof(native_record),&config));
 pid_t child=fork();assert(child>=0);
 if(!child){out=before;assert(!select_profile(&out)&&!memcmp(&out,&before,sizeof(out)));_exit(0);}
 int status;assert(waitpid(child,&status,0)==child&&WIFEXITED(status)&&!WEXITSTATUS(status));
 assert(select_profile(&out));int fd=wr_iot_service_guard_dup();assert(fd>=0&&!close(fd));
 wr_iot_service_guard_leave(1);assert(wr_iot_service_guard_dup()<0);
 puts("PASS initial generator/native saved record: ON/OFF credentials, proven-absence legacy fallback, malformed/ENOSPC/drift refusal, no writes, nested guard preservation; no driver/runtime acceptance");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-generation-saved-boot-') as directory:
 root=Path(directory)
 (root/'rc.h').write_text('int nvram_getall(char *,int,int);\nint nvram_set(const char *,const char *);\nconst char *nvram_safe_get(const char *);\nint get_ap_mode(void);\nint get_enabled_radio_rt(void);\nint is_radio_on_rt(void);\nint get_mode_radio_rt(void);\n')
 shared=here.parent/'band-steering'
 (root/'wr-band-settings-snapshot.h').write_bytes((shared/'settings-snapshot.h').read_bytes())
 (root/'check.c').write_text(body)
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2',
  '-fsanitize=address,undefined','-fno-pie','-no-pie','-DWR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED=1',
  '-DWR_IOT_NATIVE_NVRAM_SPACE=61440','-DWR_IOT_NATIVE_NVRAM_HEADER_BYTES=20',
  '-DWR_IOT_SERVICE_LOCK_PATH="'+str(root/'lock')+'"','-I'+str(root),'-I'+str(here),
  str(root/'check.c'),str(here/'rc-mode.c'),str(here/'saved-config-store.c'),
  str(here/'service-guard.c'),str(shared/'settings-snapshot.c'),'-o',str(root/'check')],check=True)
 subprocess.run([str(root/'check')],check=True,timeout=20)
