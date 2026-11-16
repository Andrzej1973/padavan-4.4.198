#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include <net/if.h>
#include "initial-restart-select.h"
#include "driver-api-client.h"
#include "rc-backend.h"
#include "rc-shutdown-admission.h"
#include "service-guard.h"
#include "request-snapshot.h"
#include "bridge.h"
#include "dns-activation.h"
static int select_unowned(void)
{
 return !wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending&&
  !wr_iot_rc_shutdown.radio_on_owned&&!wr_iot_rc_shutdown.radio_off_owned&&
  wr_iot_rc_boot_idle();
}
static int select_off(void)
{
 return select_unowned()&&wr_iot_request_initial_off_current()&&
  !if_nametoindex("br-iot")&&wr_iot_bss_is_down()&&
  wr_iot_dns_activation_recovery_state()==0;
}
enum wr_iot_initial_selection wr_iot_initial_restart_select(
 const unsigned char *nonce,struct wr_iot_idle_result *out)
{
 struct wr_iot_rc_mode a={0},b={0};struct wr_iot_idle_result first={0},last={0};
 enum wr_iot_initial_selection result=WR_INITIAL_SELECT_REFUSED;
 unsigned i,nonzero=0;int guard;
 if(!out)return result;
 memset(out,0,sizeof(*out));if(!nonce)return result;
 for(i=0;i<16;i++)nonzero|=nonce[i];
 if(!nonzero||!select_unowned())return result;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return result;
 if(!select_unowned()||!wr_iot_rc_mode_read(&a))goto done;
 /* Live radio-UP mode distinguishes this path from cold DOWN selection.
  * NATIVE is only inapplicability, never an unsuccessful driver observation. */
 if(a.router!=1||a.radio!=1||a.mode!=0){result=WR_INITIAL_SELECT_NATIVE;goto done;}
 if(!select_off()||!wr_iot_driver_initial_idle_read(nonce,&first)||
    !select_off()||!wr_iot_driver_initial_idle_read(nonce,&last)||
    !first.epoch||!first.generation||!first.serial||
    first.epoch!=last.epoch||first.generation!=last.generation||last.serial<=first.serial||
    !wr_iot_rc_mode_read(&b)||a.router!=b.router||a.radio!=b.radio||a.mode!=b.mode||
    !select_off())goto done;
 *out=last;result=WR_INITIAL_SELECT_ELIGIBLE;
 done:wr_iot_service_guard_leave(guard);return result;
}

int wr_iot_initial_restart_selected_current(const unsigned char *nonce,
 const struct wr_iot_idle_result *selected)
{
 struct wr_iot_idle_result a={0},b={0};struct wr_iot_rc_mode mode={0};
 unsigned i,nonzero=0;int fd;
 if(!nonce||!selected||!selected->epoch||!selected->generation||!selected->serial||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    wr_iot_rc_shutdown.radio_on_owned||wr_iot_rc_shutdown.radio_off_owned)return 0;
 for(i=0;i<16;i++)nonzero|=nonce[i];
 if(!nonzero)return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;
 if(close(fd))return 0;
 if(!wr_iot_rc_boot_idle()||!wr_iot_rc_mode_read(&mode)||
    mode.router!=1||mode.radio!=1||mode.mode!=0||
    !wr_iot_request_initial_off_current()||if_nametoindex("br-iot")||
    !wr_iot_bss_is_down()||wr_iot_dns_activation_recovery_state()!=0||
    !wr_iot_driver_initial_idle_read(nonce,&a)||
    !wr_iot_driver_initial_idle_read(nonce,&b)||
    a.epoch!=selected->epoch||b.epoch!=selected->epoch||
    a.generation!=selected->generation||b.generation!=selected->generation||
    a.serial<=selected->serial||b.serial<=a.serial||
    !wr_iot_rc_mode_read(&mode)||mode.router!=1||mode.radio!=1||mode.mode!=0)return 0;
 return wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending&&
  !wr_iot_rc_shutdown.radio_on_owned&&!wr_iot_rc_shutdown.radio_off_owned&&
  wr_iot_rc_boot_idle()&&wr_iot_request_initial_off_current()&&
  !if_nametoindex("br-iot")&&wr_iot_bss_is_down()&&
  wr_iot_dns_activation_recovery_state()==0;
}
