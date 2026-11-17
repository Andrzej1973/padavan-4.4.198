#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include "flash-save-attempt.h"
#include "config-snapshot-prepared.h"
#include "native-flash-prepared.h"
#if WR_IOT_NATIVE_FLASH_READBACK_PREPARED == 1 && WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <sys/ioctl.h>
#include <bcmnvram.h>
#include "native-flash-wire.h"
#include "rc.h"
#include "wr-band-settings-snapshot.h"
#endif
int wr_iot_flash_save_snapshot(const char *expected,int *manual)
{
#if WR_IOT_NATIVE_FLASH_READBACK_PREPARED == 1 && WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 struct wr_band_settings_snapshot snapshot={0};const char *record,*policy;int ok=0,value=0;
 if(getpid()<=1||!expected||!manual||wr_band_snapshot_capture(&snapshot,0x20000,nvram_getall))return 0;
 record=wr_band_snapshot_get(&snapshot,WR_IOT_SAVED_CONFIG_KEY);
 policy=wr_band_snapshot_get(&snapshot,"nvram_manual");
 if(policy&&*policy){
  if(strcmp(policy,"0")&&strcmp(policy,"1"))goto done;
  value=policy[0]=='1';
 }
 if(record&&!strcmp(record,expected)){*manual=value;ok=1;}
 done:wr_band_snapshot_release(&snapshot);return ok;
#else
 (void)expected;(void)manual;return 0;
#endif
}
int wr_iot_flash_save_commit_once(const char *expected,size_t length,
 enum wr_iot_flash_save_mode mode)
{
#if WR_IOT_NATIVE_FLASH_READBACK_PREPARED == 1 && WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 struct wr_nvram_save_profile request={0};struct stat status;int fd=-1,ret=-1,closed;
 if(getpid()<=1||!expected||!length||length>=sizeof(request.record)||
    memchr(expected,0,length)||(mode!=WR_IOT_FLASH_SAVE_AUTO&&mode!=WR_IOT_FLASH_SAVE_EXPLICIT))goto done;
 request.size=sizeof(request);request.version=1;request.record_length=length;
 request.flags=mode==WR_IOT_FLASH_SAVE_EXPLICIT?WR_NVRAM_SAVE_EXPLICIT:0;
 memcpy(request.record,expected,length);
 fd=open("/dev/nvram",O_RDWR|O_CLOEXEC|O_NOFOLLOW);
 if(fd<0)goto done;
 if(fstat(fd,&status)||!S_ISCHR(status.st_mode)||major(status.st_rdev)!=NVRAM_MAJOR)goto done;
 ret=ioctl(fd,WR_NVRAM_IOCTL_SAVE_PROFILE,&request);closed=close(fd);fd=-1;
 ret=ret||closed?-1:0;
 done:
 if(fd>=0)close(fd);
 wr_iot_saved_wipe(&request,sizeof(request));return ret;
#else
 (void)expected;(void)length;(void)mode;return -1;
#endif
}
