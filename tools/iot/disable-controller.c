#include <net/if.h>
#include <string.h>
#include "disable-controller.h"
#include "bridge.h"
int wr_iot_disable_begin(struct wr_iot_disable_controller *s){
 if(!s||s->profile_committed||s->radio.active||s->services.settings.active||s->services.committed)return 0;
 if(!wr_iot_radio_profile_take(&s->radio))return 0;
 if(!wr_iot_disable_services_begin(&s->services)){
  /* No generators or setters have run; cancel the private file capture. */
  (void)wr_iot_radio_profile_cancel(&s->radio);return 0;
 }
 if(!wr_iot_radio_profile_can_remove(&s->radio,
    s->services.settings.values[3],s->services.settings.values[4])){
  if(wr_iot_disable_services_cancel(&s->services))
   (void)wr_iot_radio_profile_cancel(&s->radio);
  return 0;
 }
 return 1;
}
int wr_iot_disable_apply_services(struct wr_iot_disable_controller *s){
 if(!s||!s->radio.active||s->profile_committed)return 0;
 /* Initial capture is not a lease on the profile path. Recheck immediately
  * before gate/service changes, including retries after service failure. */
 if(!wr_iot_radio_profile_can_remove(&s->radio,
    s->services.settings.values[3],s->services.settings.values[4]))return 0;
 return wr_iot_disable_services_apply(&s->services);
}
int wr_iot_disable_apply_profile(struct wr_iot_disable_controller *s){
 if(!s||!s->services.committed||s->profile_committed||
    if_nametoindex("br-iot")||!wr_iot_bss_is_down())return 0;
 if(!wr_iot_request_disable_ready(&s->services.settings))return 0;
 return wr_iot_radio_profile_remove_owned(&s->radio,
  s->services.settings.values[3],s->services.settings.values[4]);
}
int wr_iot_disable_commit(struct wr_iot_disable_controller *s){
 if(!s||!s->services.committed||if_nametoindex("br-iot")||!wr_iot_bss_is_down())return 0;
 if(!s->profile_committed){
  if(!wr_iot_radio_profile_commit_removed(&s->radio))return 0;
  s->profile_committed=1;
 }
 if(!wr_iot_disable_services_finish(&s->services))return 0;
 memset(s,0,sizeof(*s));return 1;
}
