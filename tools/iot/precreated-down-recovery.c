#include <string.h>
#include <unistd.h>
#include <net/if.h>
#include "precreated-down-recovery.h"
#include "precreated-down-client.h"
#include "service-guard.h"
#include "rc-shutdown-admission.h"
#include "request-snapshot.h"
#include "bridge.h"
#include "dns-activation.h"
#include "restart-main-state.h"
static int recovery_down_policy(void)
{
 return wr_iot_rc_shutdown.active&&wr_iot_rc_shutdown.radio_off_owned&&
  (wr_iot_rc_shutdown.pending==0||wr_iot_rc_shutdown.pending==SIGTERM
#ifdef SIGQUIT
   ||wr_iot_rc_shutdown.pending==SIGQUIT
#endif
  )&&wr_iot_request_initial_off_current()&&!if_nametoindex("br-iot")&&
  wr_iot_bss_is_down()&&wr_iot_dns_activation_recovery_state()==0&&
  wr_iot_restart_main_down();
}
int wr_iot_initial_down_recovery_current(const unsigned char *nonce,
 const struct wr_iot_down_result *expected)
{
 struct wr_iot_down_result baseline,before={0},after={0};int fd;
 if(!expected)return 0;
 baseline=*expected;
 if(!baseline.epoch||!baseline.generation||!baseline.main_close_serial)return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;if(close(fd))return 0;
 if(!recovery_down_policy()||!wr_iot_driver_initial_down_read(nonce,&before)||
    !recovery_down_policy()||!wr_iot_driver_initial_down_read(nonce,&after)||
    !recovery_down_policy())return 0;
 return before.epoch==baseline.epoch&&after.epoch==baseline.epoch&&
  before.generation==baseline.generation&&after.generation==baseline.generation&&
  before.main_close_serial==baseline.main_close_serial&&
  after.main_close_serial==baseline.main_close_serial;
}
