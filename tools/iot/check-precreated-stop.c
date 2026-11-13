#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include "precreated-stop.h"
static struct wr_iot_precreated_stop *current_stop;
static int depth,bridge,down,attached,isolated,services,fault,closed_ok,query_ok,closes,progresses,releases,actions;
static unsigned long long observed_serial;
static int allow(enum wr_iot_stop_phase phase){assert(depth==2&&current_stop->phase==phase);actions++;return fault!=(int)phase;}
int wr_iot_service_guard_enter(int enabled){assert(enabled);depth++;return 1;}
void wr_iot_service_guard_leave(int token){assert(token==1&&depth>0);depth--;}
int wr_iot_service_guard_dup(void){assert(depth==2);return open("/dev/null",O_RDONLY);}
int wr_iot_disable_begin_precreated(struct wr_iot_disable_controller *s){assert(depth==1);depth++;s->precreated=1;s->services.settings.active=1;return 1;}
int wr_iot_disable_services_cancel(struct wr_iot_disable_services *s){assert(depth==2&&s->settings.active);s->settings.active=0;depth--;return 1;}
int wr_iot_driver_open_recovery_read(const struct wr_iot_driver_attempt *a,struct wr_iot_driver_open_recovery_result *out){assert(depth==2&&a->request_id[0]==1);*out=(struct wr_iot_driver_open_recovery_result){1,2,3};return query_ok;}
int wr_iot_driver_close_request_from_open(struct wr_iot_driver_close_request *out,const struct wr_iot_driver_attempt *a,const struct wr_iot_driver_open_current_result *r){memcpy(out->open_request_id,a->request_id,16);out->adapter_epoch=r->adapter_epoch;out->device_generation=r->device_generation;out->open_token=r->open_token;return 1;}
enum wr_iot_driver_close_submit_result wr_iot_driver_close_submit(const struct wr_iot_driver_close_request *r){assert(r->open_request_id[0]==1&&r->open_token==3);closes++;down=1;return WR_IOT_DRIVER_CLOSE_UNCERTAIN;}
enum wr_iot_driver_close_submit_result wr_iot_driver_close_progress_submit(const struct wr_iot_driver_close_request *r){assert(r->open_token==3);progresses++;return WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;}
enum wr_iot_driver_close_submit_result wr_iot_driver_close_release_submit(const struct wr_iot_driver_close_request *r){assert(r->open_token==3);releases++;return releases%2?WR_IOT_DRIVER_CLOSE_PENDING:WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;}
int wr_iot_driver_attempt_closed(const struct wr_iot_driver_attempt *a,struct wr_iot_driver_closed_result *out){assert(a->request_id[0]==1&&depth==2);*out=(struct wr_iot_driver_closed_result){1,2,3,observed_serial};return closed_ok;}
int wr_iot_disable_services_isolate(struct wr_iot_disable_services *s){assert(s->settings.active&&bridge&&down);if(!allow(WR_IOT_STOP_ISOLATE))return 0;isolated=1;return 1;}
int wr_iot_disable_apply_services(struct wr_iot_disable_controller *s){assert(isolated&&bridge&&down);if(!allow(WR_IOT_STOP_SERVICES))return 0;s->services.committed=services=1;return 1;}
int wr_iot_bridge_set_up(int up){assert(!up&&services&&isolated&&down);return allow(WR_IOT_STOP_BRIDGE_DOWN);}
int wr_iot_bridge_detach(void){assert(services&&bridge&&down);if(!allow(WR_IOT_STOP_DETACH))return 0;attached=0;return 1;}
int wr_iot_bridge_remove(void){assert(!attached&&services&&down);if(!allow(WR_IOT_STOP_REMOVE))return 0;bridge=0;return 1;}
int wr_iot_disable_apply_reserved(struct wr_iot_disable_controller *s){assert(!bridge&&s->precreated);if(!allow(WR_IOT_STOP_APPLY))return 0;s->reserved_applied=1;return 1;}
unsigned int if_nametoindex(const char *name){assert(!strcmp(name,"br-iot"));return bridge;}
int wr_iot_bss_is_down(void){return down;}
int wr_iot_request_disable_ready(struct wr_iot_request_snapshot *s){assert(s->active&&!bridge);return allow(WR_IOT_STOP_OBSERVE);}
int wr_iot_disable_commit(struct wr_iot_disable_controller *s){assert(!bridge&&down&&s->reserved_applied&&isolated);if(!allow(WR_IOT_STOP_COMMIT))return 0;memset(s,0,sizeof(*s));depth--;return 1;}
#include "driver-close-controller.c"
#include "precreated-stop.c"
int main(void)
{
 struct wr_iot_driver_attempt attempt={{1,2},{1}};
 for(enum wr_iot_stop_phase fail=WR_IOT_STOP_ISOLATE;fail<=WR_IOT_STOP_COMMIT;fail++){
  struct wr_iot_precreated_stop s={0};current_stop=&s;
  observed_serial=4;depth=0;bridge=attached=closed_ok=query_ok=1;down=isolated=services=closes=progresses=releases=actions=fault=0;
  assert(wr_iot_precreated_stop_begin(&s,&attempt)&&depth==2);
  assert(!wr_iot_precreated_stop_begin(&s,&attempt));
  assert(!wr_iot_precreated_stop_step(&s)&&s.phase==WR_IOT_STOP_CLOSE&&closes==1);
  assert(!wr_iot_precreated_stop_cancel(&s));
  assert(!wr_iot_precreated_stop_step(&s)&&s.close.phase==WR_IOT_CLOSE_REFERENCE_RETIRED);
  assert(!wr_iot_precreated_stop_step(&s)&&s.close.phase==WR_IOT_CLOSE_RELEASE_PENDING);
  assert(!wr_iot_precreated_stop_step(&s)&&s.phase==WR_IOT_STOP_ISOLATE);
  while(s.phase<fail)assert(!wr_iot_precreated_stop_step(&s));
  enum wr_iot_stop_phase phase=s.phase;int prior_actions=actions;
  closed_ok=0;assert(!wr_iot_precreated_stop_step(&s)&&s.phase==phase&&actions==prior_actions&&depth==2);closed_ok=1;
  s.owner++;assert(!wr_iot_precreated_stop_step(&s)&&actions==prior_actions);s.owner--;
  fault=fail;assert(!wr_iot_precreated_stop_step(&s)&&s.phase==phase&&depth==2);
  assert(!memcmp(&s.attempt,&attempt,sizeof(attempt))&&s.close.request.open_token==3);
  fault=0;prior_actions=actions;observed_serial=5;
  assert(!wr_iot_precreated_stop_step(&s)&&s.phase==phase&&actions==prior_actions);
  observed_serial=4;
  for(unsigned budget=0;s.phase!=WR_IOT_STOP_COMPLETE&&budget<20;budget++)(void)wr_iot_precreated_stop_step(&s);
  assert(s.phase==WR_IOT_STOP_COMPLETE&&!depth&&!bridge&&closes==1&&progresses==1&&releases==2);
  prior_actions=actions;assert(wr_iot_precreated_stop_step(&s)&&actions==prior_actions);
 }
 struct wr_iot_precreated_stop s={0};current_stop=&s;depth=0;closes=0;
 struct wr_iot_driver_attempt invalid={0};
 assert(!wr_iot_precreated_stop_begin(&s,&invalid)&&!depth);
 assert(wr_iot_precreated_stop_begin(&s,&attempt));
 query_ok=0;assert(!wr_iot_precreated_stop_step(&s)&&s.phase==WR_IOT_STOP_CLOSE_BEGIN&&!closes);
 assert(wr_iot_precreated_stop_cancel(&s)&&!depth&&!closes&&s.phase==WR_IOT_STOP_CANCELLED);
 assert(!wr_iot_precreated_stop_step(&s));
 puts("PASS actual experimental OFF owner plus CLOSE controller: eight network-stage failures, uncertain CLOSE once, pending release, fresh config/owner refusal, retained guard/identity, ordered teardown and pre-mutation cancellation; external resources injected, no RF/runtime claim");
 return 0;
}
