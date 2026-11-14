#define _GNU_SOURCE
#include <assert.h>
#include <signal.h>
#include <string.h>
#include <unistd.h>
#include "rc-shutdown-admission.h"
#include "physical-stop-down.h"
static int depth,guard_fail,closed_fail,entropy_fail,calls,downs,aux_calls,aux_fail;
static volatile sig_atomic_t shutdowns;
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static long entropy(void *out,unsigned n,unsigned flags)
{assert(n==32&&flags==1);if(entropy_fail)return -1;memset(out,7,n);return n;}
#define WR_IOT_GETRANDOM(out,n,flags) entropy(out,n,flags)
#include "rc-physical-stop.c"
int wr_iot_service_guard_enter(int enabled)
{assert(enabled==1);if(guard_fail)return 0;depth++;return 1;}
void wr_iot_service_guard_leave(int token){assert(token==1&&depth);depth--;}
int wr_iot_rc_backend_closed(struct wr_iot_driver_closed_result *out)
{assert(depth>=1&&wr_iot_rc_shutdown.active);if(closed_fail)return 0;*out=(struct wr_iot_driver_closed_result){11,12,13,14};return 1;}
int wr_iot_rc_physical_aux_down(unsigned int slot)
{assert(depth==2&&slot<6&&!calls&&!downs);if(aux_fail)return 0;assert(slot==(unsigned)aux_calls);aux_calls++;return 1;}
static unsigned query_status=WR_STOP_RUNNING;
static enum wr_iot_physical_call_result outcome=WR_PHYSICAL_CALL_ACKNOWLEDGED;
enum wr_iot_physical_call_result wr_iot_physical_stop_call(
 const struct wr_iot_physical_stop_request *r,struct wr_iot_physical_stop_response *out)
{
 assert(depth==2&&wr_iot_rc_shutdown.active);calls++;
 assert(r->epoch==11&&r->generation==12&&r->open_token==13&&r->closed_serial==14&&r->nonce[0]==7);
 if(outcome!=WR_PHYSICAL_CALL_ACKNOWLEDGED)return outcome;
 out->identity=*r;out->identity.attempt=19;
 out->status=r->action==WR_STOP_ARM?WR_STOP_ARMED:r->action==WR_STOP_RELEASE?WR_STOP_RELEASED:query_status;
 return outcome;
}
enum wr_iot_physical_down_result wr_iot_physical_stop_down(void)
{assert(depth==2&&wr_iot_rc_shutdown.active);downs++;return WR_PHYSICAL_DOWN_UNCERTAIN;}
static void handler(int sig)
{if(!wr_iot_rc_shutdown_note(sig)){assert(!depth);shutdowns++;}}
int main(void)
{
 struct sigaction action={0};action.sa_handler=handler;sigemptyset(&action.sa_mask);
 assert(!sigaction(SIGTERM,&action,NULL));
 struct wr_iot_rc_physical_intent intent={0,0,0},out={0},bad={0,1,0};
 assert(!wr_iot_rc_physical_begin(&bad)&&!wr_iot_rc_shutdown.active);
 for(int failure=0;failure<3;failure++){
  guard_fail=failure==0;closed_fail=failure==1;entropy_fail=failure==2;
  assert(wr_iot_rc_physical_begin(&intent)&&wr_iot_rc_physical_pending());
  assert(!wr_iot_rc_physical_take(&out));wr_iot_rc_physical_step();
  assert(!wr_iot_rc_physical_pending()&&!depth&&!wr_iot_rc_shutdown.active&&!calls&&!downs);
  assert(wr_iot_rc_physical_take(&out)==-1&&!memcmp(&intent,&out,sizeof(out)));
 }
 guard_fail=closed_fail=entropy_fail=0;
 assert(wr_iot_rc_physical_begin(&intent)&&depth==1&&wr_iot_rc_shutdown.active);
 intent.restart=1; /* Stored STOP must not follow caller edits. */
 assert(!wr_iot_rc_physical_begin(&intent));
 guard_fail=1;wr_iot_rc_physical_step();assert(!calls&&depth==1);guard_fail=0;
 aux_fail=1;wr_iot_rc_physical_step();assert(!aux_calls&&!calls&&!downs);aux_fail=0;
 for(int i=0;i<6;i++)wr_iot_rc_physical_step();
 assert(aux_calls==6&&!calls&&!downs);
 closed_fail=1;wr_iot_rc_physical_step();assert(!calls&&!downs);closed_fail=0;
 wr_iot_rc_physical_step();assert(!calls&&!downs);
 outcome=WR_PHYSICAL_CALL_UNCERTAIN;wr_iot_rc_physical_step();assert(calls==1&&!downs&&depth==1);
 outcome=WR_PHYSICAL_CALL_ACKNOWLEDGED;wr_iot_rc_physical_step();assert(calls==2&&!downs);
 wr_iot_rc_physical_step();assert(downs==1);
 assert(!kill(getpid(),SIGTERM)&&!shutdowns);
 wr_iot_rc_physical_step();assert(depth==1&&downs==1&&wr_iot_rc_physical_pending());
 query_status=WR_STOP_COMPLETE;wr_iot_rc_physical_step();assert(depth==1&&!shutdowns);
 outcome=WR_PHYSICAL_CALL_UNCERTAIN;wr_iot_rc_physical_step();assert(depth==1&&!shutdowns);
 outcome=WR_PHYSICAL_CALL_ACKNOWLEDGED;wr_iot_rc_physical_step();
 assert(!depth&&!wr_iot_rc_shutdown.active&&!wr_iot_rc_physical_pending()&&shutdowns==1&&downs==1);
 assert(wr_iot_rc_physical_take(&out)==1&&out.restart==0&&out.radio_on==0&&out.reload==0);
 assert(!wr_iot_rc_physical_take(&out));
 /* A successful restart's physical RELEASE must retain both guards and intent;
  * neither repeated steps nor terminal consumption can skip the resume gate. */
 calls=downs=aux_calls=0;shutdowns=0;intent=(struct wr_iot_rc_physical_intent){1,1,1};
 assert(wr_iot_rc_physical_begin(&intent));
 for(unsigned i=0;i<20&&wr_iot_rc_physical_pending();i++)wr_iot_rc_physical_step();
 assert(!wr_iot_rc_physical_pending()&&depth==1&&wr_iot_rc_shutdown.active&&downs==1);
 assert(wr_iot_rc_physical_restart_ready(&out)&&out.restart&&out.radio_on&&out.reload);
 assert(!wr_iot_rc_physical_take(&out));
 int previous=calls;wr_iot_rc_physical_step();assert(calls==previous&&depth==1);
 assert(!kill(getpid(),SIGTERM)&&!shutdowns);
 assert(wr_iot_rc_physical_restart_ready(&out)&&depth==1&&!shutdowns);
 /* Process exit ends this injected fixture; no production cleanup bypass. */
 return 0;
}
