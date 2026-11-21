#define _GNU_SOURCE
#include <string.h>
#include <net/if.h>
#include "rc-boot.h"
#include "control-channel.h"
#include "rc-backend.h"
#include "rc-shutdown-admission.h"
#include "service-guard.h"
#include "driver-api-client.h"
#include "request-snapshot.h"
#include "bridge.h"
#include "dns-activation.h"
#include "precreated-entropy.h"
static int boot_armed,boot_spent;
static unsigned long long boot_retry;
void wr_iot_rc_boot_arm(void){boot_armed=1;}
int wr_iot_rc_boot_pending(void){return boot_armed&&!boot_spent;}
static int boot_unowned(void)
{
 return !wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending&&
  !wr_iot_rc_shutdown.radio_off_owned&&!wr_iot_rc_shutdown.radio_on_owned;
}
static int boot_off_policy(void)
{
 return boot_unowned()&&wr_iot_request_initial_off_current()&&
  !if_nametoindex("br-iot")&&wr_iot_bss_is_down()&&wr_iot_dns_activation_recovery_state()==0;
}
static void boot_wipe(void *p,size_t n){volatile unsigned char*b=p;while(n--)*b++=0;}
int wr_iot_rc_boot_step(void)
{
 static const char hex[]="0123456789abcdef";
 struct wr_iot_control_request request={0};struct wr_iot_request after={0};
 struct wr_iot_rc_mode mode={0};struct wr_iot_idle_result a={0},b={0};
 struct wr_iot_mailbox mailbox;unsigned char bytes[32]={0};
 unsigned long long now;unsigned i,nonzero=0;int guard,ready=0,submitted=0;
 if(!wr_iot_rc_boot_pending()||!boot_unowned())return 0;
 now=wr_iot_control_now();if(!now||(boot_retry&&now<boot_retry))return 0;
 boot_retry=now+1;
 if(!wr_iot_rc_boot_idle()){boot_spent=1;return 0;}
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 if(!boot_unowned()||!wr_iot_rc_radio_on_mode_read(&mode))goto release;
 if(mode.router!=1||mode.radio!=1||mode.mode!=0){boot_spent=1;goto release;}
 /* Saved radio OFF is a deliberate skip. A saved-ON radio still coming up
  * must remain pending without publishing or executing an activation. */
 if(!wr_iot_rc_mode_read(&mode)||mode.router!=1||mode.radio!=1||mode.mode!=0)goto release;
 if(!wr_iot_rc_radio_on_saved_request(&request.request)||!request.request.enabled){boot_spent=1;goto release;}
 if(!boot_off_policy()||!wr_iot_rc_boot_idle()){boot_spent=1;goto release;}
 if(wr_iot_precreated_entropy(NULL,bytes,sizeof(bytes))!=(int)sizeof(bytes))goto release;
 for(i=0;i<16;i++)nonzero|=bytes[i];
 if(!nonzero)goto release;
 if(!wr_iot_driver_initial_idle_read(bytes,&a)||!boot_off_policy()||
    !wr_iot_driver_initial_idle_read(bytes,&b)||!boot_off_policy()||
    !a.epoch||!a.generation||!a.serial||a.epoch!=b.epoch||a.generation!=b.generation||b.serial<=a.serial||
    !wr_iot_rc_radio_on_saved_request(&after)||memcmp(&after,&request.request,sizeof(after))||
    !wr_iot_rc_mode_read(&mode)||mode.router!=1||mode.radio!=1||mode.mode!=0||!wr_iot_rc_boot_idle())goto release;
 for(i=0;i<16;i++){request.id[2*i]=hex[bytes[i]>>4];request.id[2*i+1]=hex[bytes[i]&15];}
 request.created=now;ready=1;
 release:wr_iot_service_guard_leave(guard);
 /* Queue and service guards are never nested. Once a publication is attempted,
  * ambiguous files must remain owned by the normal mailbox protocol. */
 if(ready&&boot_unowned()){
  wr_iot_mailbox_init(&mailbox);
  if(wr_iot_mailbox_open(&mailbox,WR_IOT_CONTROL_DIRECTORY,1)){
   boot_spent=1;submitted=wr_iot_mailbox_submit_initial(&mailbox,&request);
   wr_iot_mailbox_close(&mailbox);
  }
 }
 boot_wipe(&after,sizeof(after));boot_wipe(&request,sizeof(request));boot_wipe(bytes,sizeof(bytes));return submitted;
}
