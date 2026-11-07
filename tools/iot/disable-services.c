#include <string.h>
#include "disable-services.h"
#include "dns-activation.h"
int wr_iot_disable_services_begin(struct wr_iot_disable_services *s){
 if(!s||s->committed||s->settings.active||s->settings.token)return 0;
 return wr_iot_request_disable_take(&s->settings);
}
int wr_iot_disable_services_apply(struct wr_iot_disable_services *s){
 if(!s||!wr_iot_request_disable_close_gates(&s->settings))return 0;
 /* This is a receipt for this synchronous step, not a live health verdict.
  * The outer controller's OBSERVE must still verify all current resources. */
 if(s->committed)return 1;
 if(wr_iot_dns_disable_prepare()!=0)return 0;
 if(wr_iot_dns_disable_commit()!=1)return 0;
 s->committed=1;return 1;
}
int wr_iot_disable_services_cancel(struct wr_iot_disable_services *s){
 if(!s||s->committed||!wr_iot_request_disable_cancel(&s->settings))return 0;
 memset(s,0,sizeof(*s));return 1;
}
int wr_iot_disable_services_finish(struct wr_iot_disable_services *s){
 if(!s||!s->committed||!wr_iot_request_disable_forget(&s->settings))return 0;
 if(!wr_iot_request_snapshot_finish(&s->settings))return 0;
 memset(s,0,sizeof(*s));return 1;
}
