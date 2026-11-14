#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include "restart-profile.h"
#include "precreated-profile-request.h"
#include "radio-profile-state.h"
#include "service-guard.h"
#include "rc.h"
static const char *profile_saved_read(void *unused,const char *key)
{(void)unused;return nvram_safe_get(key);}
static int profile_guard(void)
{int fd=wr_iot_service_guard_dup();return fd>=0&&close(fd)==0;}
static void profile_wipe(void *data,size_t length)
{volatile unsigned char *p=data;while(length--)*p++=0;}
int wr_iot_restart_profile_current(const struct wr_iot_request *desired)
{
 struct wr_iot_precreated_profile_request before={0},after={0};
 struct wr_iot_saved_file first={0},second={0};struct stat current;
 int ok=0;
 if(!desired||desired->enabled!=1||
    !memchr(desired->ssid,0,sizeof(desired->ssid))||
    !memchr(desired->password,0,sizeof(desired->password))||!profile_guard())return 0;
 if(!wr_iot_precreated_profile_request_read(&before,profile_saved_read,NULL)||
    strcmp(before.ssid,desired->ssid)||strcmp(before.password,desired->password))goto done;
 if(!wr_iot_saved_capture(&first,WR_IOT_RADIO_PROFILE_PATH)||!first.existed||!first.size||
    !wr_iot_profile_disable_buffer(first.data,first.size,desired->ssid,desired->password))goto done;
 /* Independent byte readback under the same caller-owned guard. The scanner
  * above performs no transformation/write despite its historical name. */
 if(!wr_iot_saved_capture(&second,WR_IOT_RADIO_PROFILE_PATH)||!second.existed||
    first.size!=second.size||first.metadata.st_dev!=second.metadata.st_dev||
    first.metadata.st_ino!=second.metadata.st_ino||
    first.metadata.st_mtime!=second.metadata.st_mtime||
    first.metadata.st_ctime!=second.metadata.st_ctime||memcmp(first.data,second.data,first.size)||
    !wr_iot_precreated_profile_request_read(&after,profile_saved_read,NULL)||
    before.requested_enabled!=after.requested_enabled||strcmp(before.ssid,after.ssid)||
    strcmp(before.password,after.password)||!profile_guard()||
    lstat(WR_IOT_RADIO_PROFILE_PATH,&current)||!S_ISREG(current.st_mode)||
    current.st_dev!=second.metadata.st_dev||current.st_ino!=second.metadata.st_ino||
    current.st_size!=second.metadata.st_size||current.st_mtime!=second.metadata.st_mtime||
    current.st_ctime!=second.metadata.st_ctime)goto done;
 ok=1;
 done:
 if(first.data)profile_wipe(first.data,first.size);
 if(second.data)profile_wipe(second.data,second.size);
 wr_iot_saved_release(&first);wr_iot_saved_release(&second);
 profile_wipe(&before,sizeof(before));profile_wipe(&after,sizeof(after));return ok;
}
