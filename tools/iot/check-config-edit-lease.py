from pathlib import Path
import subprocess
import tempfile
here=Path(__file__).resolve().parent
shared=here.parent/'band-steering'
prefix=(here/'check-config-edit-pin.c').read_text().split('int main(void)')[0]
body=r'''
#include "config-edit-lease.h"
static int entropy_mode,entropy_calls;
static int entropy(void *context,unsigned char *bytes,unsigned int length)
{
 assert(!context&&length==32);entropy_calls++;
 memset(bytes,entropy_mode==2?0:0x5a,length);
 return entropy_mode==1?31:entropy_mode==3?-1:32;
}
int main(void)
{
 struct wr_iot_config_edit_lease lease={0},copy,empty={0};
 struct wr_iot_config_view view,before_view;
 struct wr_iot_saved_config config={.profile={.enabled=0,.ssid="IoT",
 .password="private-key",.gateway="192.168.50.1",.mask="255.255.255.0",
 .first="192.168.50.20",.last="192.168.50.200"}},fields,out,before;
 char revision[33],original[33];int mode;
 assert(wr_iot_saved_config_encode(native_record,sizeof(native_record),&config));
 memset(&view,0x5a,sizeof(view));before_view=view;
 memset(revision,'x',sizeof(revision));memcpy(original,revision,sizeof(original));
 assert(wr_iot_service_guard_enter(1)==1);
 for(mode=1;mode<=3;mode++){
  entropy_mode=mode;
  assert(!wr_iot_config_edit_lease_open(&lease,10,30,entropy,NULL,&view,revision));
  assert(!memcmp(&lease,&empty,sizeof(lease))&&!memcmp(&view,&before_view,sizeof(view))&&
         !memcmp(revision,original,sizeof(revision)));
 }
 entropy_mode=0;
 assert(!wr_iot_config_edit_lease_open(&lease,10,301,entropy,NULL,&view,revision));
 assert(!wr_iot_config_edit_lease_open(&lease,~0ULL,30,entropy,NULL,&view,revision));
 assert(wr_iot_config_edit_lease_open(&lease,10,30,entropy,NULL,&view,revision));
 copy=lease;assert(!wr_iot_config_edit_lease_open(&lease,11,30,entropy,NULL,&view,revision));
 fields=config;memset(fields.profile.password,0,sizeof(fields.profile.password));
 memset(&out,0x5a,sizeof(out));before=out;
 assert(!wr_iot_config_edit_lease_claim(&copy,revision,11,&fields,WR_IOT_CONFIG_KEY_KEEP,&out));
 assert(!wr_iot_config_edit_lease_claim(&lease,"ffffffffffffffffffffffffffffffff",11,&fields,WR_IOT_CONFIG_KEY_KEEP,&out));
 assert(lease.phase==WR_IOT_EDIT_LEASE_LIVE&&!memcmp(&out,&before,sizeof(out)));
 assert(wr_iot_config_edit_lease_claim(&lease,revision,11,&fields,WR_IOT_CONFIG_KEY_KEEP,&out));
 assert(!strcmp(out.profile.password,"private-key"));out=before;
 assert(!wr_iot_config_edit_lease_claim(&lease,revision,12,&fields,WR_IOT_CONFIG_KEY_KEEP,&out));
 assert(!memcmp(&out,&before,sizeof(out)));assert(wr_iot_config_edit_lease_release(&lease));
 assert(!memcmp(&lease,&empty,sizeof(lease)));
 assert(wr_iot_config_edit_lease_open(&lease,10,30,entropy,NULL,&view,revision));
 assert(!wr_iot_config_edit_lease_claim(&lease,revision,40,&fields,WR_IOT_CONFIG_KEY_KEEP,&out));
 assert(!wr_iot_config_edit_lease_claim(&lease,revision,11,&fields,WR_IOT_CONFIG_KEY_KEEP,&out));
 assert(wr_iot_config_edit_lease_release(&lease));
 assert(wr_iot_config_edit_lease_open(&lease,10,30,entropy,NULL,&view,revision));
 assert(!wr_iot_config_edit_lease_claim(&lease,revision,9,&fields,WR_IOT_CONFIG_KEY_KEEP,&out));
 assert(wr_iot_config_edit_lease_release(&lease));
 assert(wr_iot_config_edit_lease_open(&lease,10,30,entropy,NULL,&view,revision));
 read_error=1;assert(!wr_iot_config_edit_lease_claim(&lease,revision,11,&fields,WR_IOT_CONFIG_KEY_KEEP,&out));
 read_error=0;assert(!wr_iot_config_edit_lease_claim(&lease,revision,12,&fields,WR_IOT_CONFIG_KEY_KEEP,&out));
 assert(wr_iot_config_edit_lease_release(&lease));
 assert(!memcmp(&out,&before,sizeof(out)));
 wr_iot_service_guard_leave(1);
 puts("PASS bounded edit lease with actual pin/store/guard: checked entropy, expiry/clock regression, single claim, stale/copy/error refusal and wipe; no write or endpoint binding");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-edit-lease-') as directory:
 root=Path(directory);source=root/'check.c';source.write_text(prefix+body)
 (root/'rc.h').write_text('int nvram_getall(char *,int,int);\nint nvram_set(const char *,const char *);\n')
 (root/'wr-band-settings-snapshot.h').write_bytes((shared/'settings-snapshot.h').read_bytes())
 binary=root/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2',
  '-fsanitize=address,undefined','-fno-pie','-no-pie',
  '-DWR_IOT_NATIVE_NVRAM_SPACE=61440','-DWR_IOT_NATIVE_NVRAM_HEADER_BYTES=20',
  '-DWR_IOT_SERVICE_LOCK_PATH="'+str(root/'lock')+'"',
  '-DWR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED=1','-I'+str(root),'-I'+str(here),
  str(here/'saved-config-store.c'),str(here/'service-guard.c'),
  str(shared/'settings-snapshot.c'),str(source),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=15)
