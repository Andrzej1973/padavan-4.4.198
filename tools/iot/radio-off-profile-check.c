#include <string.h>
#include <unistd.h>
#include "radio-off-profile.h"
#include "restart-profile.h"
#include "precreated-profile-request.h"
#include "rc.h"
static const char *off_profile_read(void *unused,const char *key)
{(void)unused;return nvram_safe_get(key);}
static void off_profile_wipe(void *p,size_t n)
{volatile unsigned char *b=p;while(n--)*b++=0;}
int wr_iot_rc_off_profile_current(void)
{
 struct wr_iot_precreated_profile_request saved={0};
 struct wr_iot_request desired={0};int ok=0;
 if(!wr_iot_radio_profile_guard()||
    !wr_iot_precreated_profile_request_read(&saved,off_profile_read,NULL))goto done;
 /* enabled=1 selects the existing profile scanner; no request is submitted.
  * Cold third BSS remains inactive; saved runtime OFF is not rewritten. */
 desired.enabled=1;
 memcpy(desired.ssid,saved.ssid,sizeof(desired.ssid));
 memcpy(desired.password,saved.password,sizeof(desired.password));
 ok=wr_iot_restart_profile_current(&desired);
 done:off_profile_wipe(&desired,sizeof(desired));off_profile_wipe(&saved,sizeof(saved));return ok;
}
