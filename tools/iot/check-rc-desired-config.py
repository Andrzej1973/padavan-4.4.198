#!/usr/bin/env python3
"""Actual RC selection plus actual native desired reader, external SDK actors."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
body=r'''
#define nvram_getall fixture_native_getall
#define main store_fixture_main
#include "check-saved-config-store.c"
#undef main
#undef nvram_getall
#include "rc-backend.h"
static int legacy_reads,radio_enabled=1,ap_mode;
static int change_on_read,snapshot_calls;
int nvram_getall(char *out,int capacity,int temporary){
 int result=fixture_native_getall(out,capacity,temporary);
 if(++snapshot_calls==change_on_read){
  struct wr_iot_saved_config next=config;strcpy(next.profile.ssid,"Concurrent replacement");
  assert(wr_iot_saved_config_encode(native_record,sizeof(native_record),&next));present=1;
 }
 return result;
}
int get_ap_mode(void){return ap_mode;}
int get_enabled_radio_rt(void){return radio_enabled;}
int is_radio_on_rt(void){return 0;}
int get_mode_radio_rt(void){return 0;}
const char *nvram_safe_get(const char *key){legacy_reads++;assert(!strcmp(key,"wr_iot_enable"));return "0";}
int main(void){
 struct wr_iot_request out={.enabled=7},before=out;
 reset();assert(!wr_iot_rc_radio_on_saved_request(&out)&&!memcmp(&out,&before,sizeof(out)));
 assert(wr_iot_service_guard_enter(1)==1);
 assert(wr_iot_rc_radio_on_saved_request(&out)&&!out.enabled&&legacy_reads);
 legacy_reads=0;present=1;config.profile.enabled=1;
 assert(wr_iot_saved_config_encode(native_record,sizeof(native_record),&config));
 assert(wr_iot_rc_radio_on_saved_request(&out)&&out.enabled==1&&!legacy_reads);
 assert(!strcmp(out.ssid,config.profile.ssid)&&!strcmp(out.password,config.profile.password));
 config.profile.enabled=0;assert(wr_iot_saved_config_encode(native_record,sizeof(native_record),&config));
 assert(wr_iot_rc_radio_on_saved_request(&out)&&!out.enabled&&!out.ssid[0]&&!legacy_reads);
 out=before;read_error=1;assert(!wr_iot_rc_radio_on_saved_request(&out)&&!memcmp(&out,&before,sizeof(out))&&!legacy_reads);
 read_error=0;strcpy(native_record,"malformed");
 assert(!wr_iot_rc_radio_on_saved_request(&out)&&!memcmp(&out,&before,sizeof(out))&&!legacy_reads);
 /* A write between the two coherent reads must not select either revision. */
 config.profile.enabled=1;assert(wr_iot_saved_config_encode(native_record,sizeof(native_record),&config));
 snapshot_calls=0;change_on_read=1;
 assert(!wr_iot_rc_radio_on_saved_request(&out)&&!memcmp(&out,&before,sizeof(out))&&!legacy_reads);
 /* Absence becoming present also refuses instead of falling back to legacy. */
 present=0;snapshot_calls=0;
 assert(!wr_iot_rc_radio_on_saved_request(&out)&&!memcmp(&out,&before,sizeof(out))&&!legacy_reads);
 change_on_read=0;
 radio_enabled=0;assert(!wr_iot_rc_radio_on_saved_request(&out)&&!memcmp(&out,&before,sizeof(out)));
 radio_enabled=1;ap_mode=1;assert(!wr_iot_rc_radio_on_saved_request(&out)&&!memcmp(&out,&before,sizeof(out)));
 wr_iot_service_guard_leave(1);
 puts("PASS actual RC desired selection: complete new ON, empty runtime OFF, legacy only for proven absence, malformed/error/mode/guard refuse unchanged; actual native store/guard/snapshot with SDK syscall actors");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-rc-desired-') as d:
 root=Path(d);(root/'rc.h').write_text('int nvram_getall(char *,int,int);\nint nvram_set(const char *,const char *);\nconst char *nvram_safe_get(const char *);\nint get_ap_mode(void);\nint get_enabled_radio_rt(void);\nint is_radio_on_rt(void);\nint get_mode_radio_rt(void);\n')
 (root/'wr-band-settings-snapshot.h').write_bytes((here.parent/'band-steering/settings-snapshot.h').read_bytes())
 (root/'check.c').write_text(body)
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-DWR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED=1','-DWR_IOT_NATIVE_NVRAM_SPACE=61440','-DWR_IOT_NATIVE_NVRAM_HEADER_BYTES=20','-DWR_IOT_SERVICE_LOCK_PATH="'+str(root/'lock')+'"','-I'+d,'-I'+str(here),str(root/'check.c'),str(here/'rc-mode.c'),str(here/'saved-config-store.c'),str(here/'service-guard.c'),str(here.parent/'band-steering/settings-snapshot.c'),'-o',str(root/'check')],check=True)
 subprocess.run([str(root/'check')],check=True,timeout=15)
