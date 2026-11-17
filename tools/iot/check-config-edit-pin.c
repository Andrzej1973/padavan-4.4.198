#include <assert.h>
#include <stdio.h>
#include <unistd.h>
#include <sys/wait.h>
#include "config-edit-pin.h"
#include "service-guard.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static char native_record[WR_IOT_SAVED_CONFIG_MAX];
static int present=1,read_error,reads,drift_after_read;
int nvram_getall(char *out,int capacity,int temporary)
{
 assert(capacity==0x20000&&temporary==1);reads++;
 if(read_error)return -1;
 memset(out,0,(size_t)capacity);
 if(present)snprintf(out,(size_t)capacity,"%s=%s",WR_IOT_SAVED_CONFIG_KEY,native_record);
 if(drift_after_read){native_record[0]='X';drift_after_read=0;}
 return 0;
}
int nvram_set(const char *key,const char *value)
{(void)key;(void)value;assert(0);return -1;}
int main(void)
{
 const char *id="0123456789abcdef0123456789abcdef";
 struct wr_iot_generation_config pin={0};
 struct wr_iot_config_view view,before_view;
 struct wr_iot_saved_config config={.profile={.enabled=0,.ssid="IoT",
 .password="private-key-one",.gateway="192.168.50.1",.mask="255.255.255.0",
 .first="192.168.50.20",.last="192.168.50.200"}};
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 struct wr_iot_generation_config copy;
 struct wr_iot_saved_config fields,out,before;
#endif
 assert(wr_iot_saved_config_encode(native_record,sizeof(native_record),&config));
 memset(&view,0x5a,sizeof(view));before_view=view;
 assert(!wr_iot_config_edit_capture_view(&pin,id,1,&view));
 assert(!memcmp(&view,&before_view,sizeof(view))&&!reads);
 assert(wr_iot_service_guard_enter(1)==1);
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED != 1
 assert(!wr_iot_config_edit_capture_view(&pin,id,1,&view)&&!reads);
 assert(!memcmp(&view,&before_view,sizeof(view)));
#else
 {
  struct wr_iot_generation_config empty={0};
  read_error=1;assert(!wr_iot_config_edit_capture_view(&pin,id,1,&view));read_error=0;
  assert(!memcmp(&view,&before_view,sizeof(view))&&!memcmp(&pin,&empty,sizeof(pin)));
  drift_after_read=1;assert(!wr_iot_config_edit_capture_view(&pin,id,1,&view));
  assert(!memcmp(&view,&before_view,sizeof(view))&&!memcmp(&pin,&empty,sizeof(pin)));
  assert(wr_iot_saved_config_encode(native_record,sizeof(native_record),&config));
 }
 assert(wr_iot_config_edit_capture_view(&pin,id,1,&view)&&view.key_present&&!view.enabled);
 before_view=view;copy=pin;
 assert(!wr_iot_config_edit_capture_view(&pin,id,2,&view));
 assert(!memcmp(&pin,&copy,sizeof(pin))&&!memcmp(&view,&before_view,sizeof(view)));
 fields=config;memset(fields.profile.password,0,sizeof(fields.profile.password));
 strcpy(fields.profile.ssid,"Edited IoT");memset(&out,0x5a,sizeof(out));before=out;
 assert(wr_iot_config_edit_resolve_pin(&pin,id,1,&fields,WR_IOT_CONFIG_KEY_KEEP,&out));
 assert(!strcmp(out.profile.password,"private-key-one")&&!strcmp(out.profile.ssid,"Edited IoT"));
 copy=pin;out=before;
 assert(!wr_iot_config_edit_resolve_pin(&copy,id,1,&fields,WR_IOT_CONFIG_KEY_KEEP,&out));
 assert(!wr_iot_config_edit_resolve_pin(&pin,id,2,&fields,WR_IOT_CONFIG_KEY_KEEP,&out));
 assert(!wr_iot_config_edit_resolve_pin(&pin,"ffffffffffffffffffffffffffffffff",1,&fields,WR_IOT_CONFIG_KEY_KEEP,&out));
 assert(!memcmp(&out,&before,sizeof(out)));
 {
  pid_t child=fork();int status;assert(child>=0);
  if(!child)_exit(wr_iot_config_edit_resolve_pin(&pin,id,1,&fields,WR_IOT_CONFIG_KEY_KEEP,&out)?1:0);
  assert(waitpid(child,&status,0)==child&&WIFEXITED(status)&&!WEXITSTATUS(status));
 }
 strcpy(config.profile.password,"private-key-two");
 assert(wr_iot_saved_config_encode(native_record,sizeof(native_record),&config));
 assert(!wr_iot_config_edit_resolve_pin(&pin,id,1,&fields,WR_IOT_CONFIG_KEY_KEEP,&out));
 assert(!memcmp(&out,&before,sizeof(out)));
 read_error=1;assert(!wr_iot_config_edit_resolve_pin(&pin,id,1,&fields,WR_IOT_CONFIG_KEY_REPLACE,&out));
 read_error=0;assert(wr_iot_generation_config_release(&pin));present=0;
 assert(wr_iot_config_edit_capture_view(&pin,id,3,&view)&&!view.key_present&&!view.enabled&&!view.ssid[0]);
 assert(!wr_iot_config_edit_resolve_pin(&pin,id,3,&fields,WR_IOT_CONFIG_KEY_KEEP,&out));
 strcpy(fields.profile.password,"replacement-key");
 assert(wr_iot_config_edit_resolve_pin(&pin,id,3,&fields,WR_IOT_CONFIG_KEY_REPLACE,&out));
 present=1;assert(!wr_iot_config_edit_resolve_pin(&pin,id,3,&fields,WR_IOT_CONFIG_KEY_REPLACE,&out));
 assert(wr_iot_generation_config_release(&pin));
#endif
 wr_iot_service_guard_leave(1);
 puts("PASS actual desired pin/edit/view with native snapshot parser and service guard: stale/copy/fork/error/absence gates, no SET or HTTP acceptance");
 return 0;
}
