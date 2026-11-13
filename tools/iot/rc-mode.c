/* Staged RC-only mode adapter. No physical radio operation. */
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
