#define _GNU_SOURCE
#include <string.h>
#include <net/if.h>
#include "cold-on-select.h"
#include "precreated-down-client.h"
#include "physical-stop-wire.h"
#include "rc-runtime.h"
#include "rc-backend.h"
#include "rc-shutdown-admission.h"
#include "service-guard.h"
#include "request-snapshot.h"
#include "restart-main-state.h"
#include "bridge.h"
#include "dns-activation.h"
static int cold_select_unowned(void)
{
 struct wr_iot_physical_stop_request receipt={0};
 return !wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending&&
  !wr_iot_rc_shutdown.radio_off_owned&&!wr_iot_rc_shutdown.radio_on_owned&&
  !wr_iot_rc_radio_off_receipt(&receipt);
}
static int cold_select_down(void)
{
 return cold_select_unowned()&&wr_iot_request_initial_off_current()&&
  !if_nametoindex("br-iot")&&wr_iot_bss_is_down()&&
  wr_iot_dns_activation_recovery_state()==0&&wr_iot_restart_main_down();
}
enum wr_iot_cold_selection wr_iot_cold_select(const unsigned char *nonce,
 struct wr_iot_down_result *out)
{
 struct wr_iot_rc_mode before={0},after={0};struct wr_iot_down_result a={0},b={0};
 unsigned i,nonzero=0;int guard;enum wr_iot_cold_selection result=WR_COLD_SELECT_REFUSED;
 if(!out)return result;
 memset(out,0,sizeof(*out));if(!nonce)return result;
 for(i=0;i<16;i++)nonzero|=nonce[i];
 if(!nonzero||!cold_select_unowned())return result;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return result;
 if(!cold_select_unowned()||!wr_iot_rc_radio_on_mode_read(&before))goto done;
 if(before.router!=1||before.radio!=1||before.mode!=0){result=WR_COLD_SELECT_NATIVE;goto done;}
 if(!wr_iot_restart_main_down()){result=WR_COLD_SELECT_NATIVE;goto done;}
 if(!cold_select_down())goto done;
 /* An absent DOWN endpoint/provenance leaves the pre-existing native guard
  * responsible for first startup. A successful first read followed by drift
  * is a refusal, never a reason to fall through to native restart. */
 if(!wr_iot_driver_initial_down_read(nonce,&a)){result=WR_COLD_SELECT_NATIVE;goto done;}
 if(!a.epoch||!a.generation||!a.main_close_serial||!cold_select_down()||
    !wr_iot_driver_initial_down_read(nonce,&b)||!cold_select_down()||
    a.epoch!=b.epoch||a.generation!=b.generation||a.main_close_serial!=b.main_close_serial||
    !wr_iot_rc_radio_on_mode_read(&after)||before.router!=after.router||
    before.radio!=after.radio||before.mode!=after.mode)goto done;
 *out=b;result=WR_COLD_SELECT_ELIGIBLE;
 done:
 if(!cold_select_unowned()){memset(out,0,sizeof(*out));result=WR_COLD_SELECT_REFUSED;}
 wr_iot_service_guard_leave(guard);return result;
}
