#include <string.h>
#include <unistd.h>
#include <net/if.h>
#include "precreated-down-observe.h"
#include "service-guard.h"
#include "rc-shutdown-admission.h"
#include "request-snapshot.h"
#include "bridge.h"
#include "dns-activation.h"
#include "restart-main-state.h"
static int down_policy(void)
{
 return wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending&&
  wr_iot_request_initial_off_current()&&!if_nametoindex("br-iot")&&
  wr_iot_bss_is_down()&&wr_iot_dns_activation_recovery_state()==0&&
  wr_iot_restart_main_down();
}
int wr_iot_initial_down_observe(const unsigned char *nonce,struct wr_iot_down_result *out)
{
 struct wr_iot_down_result before={0},after={0};int fd;
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;if(close(fd))return 0;
 if(!down_policy()||!wr_iot_driver_initial_down_read(nonce,&before)||
    !down_policy()||!wr_iot_driver_initial_down_read(nonce,&after)||
    !before.epoch||!before.generation||!before.main_close_serial||
    before.epoch!=after.epoch||before.generation!=after.generation||
    before.main_close_serial!=after.main_close_serial||!down_policy())return 0;
 *out=after;return 1;
}

int wr_iot_initial_down_current(const unsigned char *nonce,
 const struct wr_iot_down_result *expected)
{
 struct wr_iot_down_result baseline,current={0};
 if(!expected)return 0;
 baseline=*expected;
 if(!baseline.epoch||!baseline.generation||!baseline.main_close_serial)return 0;
 return wr_iot_initial_down_observe(nonce,&current)&&
  baseline.epoch==current.epoch&&baseline.generation==current.generation&&
  baseline.main_close_serial==current.main_close_serial;
}
