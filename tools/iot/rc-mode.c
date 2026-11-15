/* Staged RC-only mode adapter. No physical radio operation. */
#include <stdio.h>
#include <unistd.h>
#include "rc.h"
#include "rc-backend.h"
#include "service-guard.h"
int wr_iot_rc_mode_read(struct wr_iot_rc_mode *out)
{
 struct wr_iot_rc_mode current;int fd;
 if(!out)return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;
 if(close(fd))return 0;
 current.router=get_ap_mode()?0:1;
 current.radio=get_enabled_radio_rt()==1&&is_radio_on_rt()?1:0;
 current.mode=get_mode_radio_rt();
 *out=current;return 1;
}

/* OFF-to-ON admission needs saved policy, never a live-UP prerequisite.
 * Physical DOWN and subsequent new-Main identity are separate observations. */
int wr_iot_rc_radio_on_mode_read(struct wr_iot_rc_mode *out)
{
 struct wr_iot_rc_mode current;int fd;
 if(!out)return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;
 if(close(fd))return 0;
 current.router=get_ap_mode()?0:1;
 current.radio=get_enabled_radio_rt()==1?1:0;
 current.mode=get_mode_radio_rt();
 *out=current;return 1;
}

#include <string.h>
#include "request.h"
static const char *radio_saved_read(void *unused,const char *key)
{(void)unused;return nvram_safe_get(key);}
int wr_iot_rc_radio_on_saved_request(struct wr_iot_request *out)
{
 struct wr_iot_request before={0},after={0};struct wr_iot_rc_mode a={0},b={0};
 volatile unsigned char *wipe;size_t n;int ok=0;
 if(!out||!wr_iot_rc_radio_on_mode_read(&a)||a.router!=1||a.radio!=1||a.mode!=0)goto done;
 if(!wr_iot_request_read(&before,radio_saved_read,NULL,1,1,0,NULL,0)||
    !wr_iot_request_read(&after,radio_saved_read,NULL,1,1,0,NULL,0)||
    memcmp(&before,&after,sizeof(before))||!wr_iot_rc_radio_on_mode_read(&b)||
    a.router!=b.router||a.radio!=b.radio||a.mode!=b.mode)goto done;
 *out=before;ok=1;
 done:wipe=(volatile unsigned char*)&before;n=sizeof(before);while(n--)*wipe++=0;
 wipe=(volatile unsigned char*)&after;n=sizeof(after);while(n--)*wipe++=0;return ok;
}
