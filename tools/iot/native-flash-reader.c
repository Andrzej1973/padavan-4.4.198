#include "native-flash-reader.h"
#include "config-snapshot-prepared.h"
#include "native-flash-prepared.h"
#if WR_IOT_NATIVE_FLASH_READBACK_PREPARED == 1 && WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <sys/ioctl.h>
#include <bcmnvram.h>
#include "native-flash-wire.h"
#endif

enum wr_iot_flash_config_result wr_iot_native_flash_compare(
 const char *expected,size_t length)
{
#if WR_IOT_NATIVE_FLASH_READBACK_PREPARED == 1 && WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 struct stat status;anvram_ioctl_t request={0};
 unsigned char *image=NULL;int fd=-1,ok=0;
 struct wr_iot_saved_config checked={0};
 enum wr_iot_flash_config_result result=WR_IOT_FLASH_CONFIG_INVALID;
 if(WR_IOT_NATIVE_NVRAM_SPACE<24||WR_IOT_NATIVE_NVRAM_SPACE>0x20000||
    !wr_iot_saved_config_decode(&checked,expected,length))goto done;
 fd=open("/dev/nvram",O_RDONLY|O_CLOEXEC|O_NOFOLLOW);
 if(fd<0||fstat(fd,&status)||!S_ISCHR(status.st_mode)||
    major(status.st_rdev)!=NVRAM_MAJOR)goto done;
 image=malloc(WR_IOT_NATIVE_NVRAM_SPACE);
 if(!image)goto done;
 request.size=sizeof(request);request.len_value=WR_IOT_NATIVE_NVRAM_SPACE;
 request.value=(char *)image;
 /* No retry and no fallback to native RAM GETALL on unsupported ioctl. */
 ok=ioctl(fd,WR_NVRAM_IOCTL_READ_FLASH,&request)==0;
 if(close(fd))ok=0;
 fd=-1;
 if(ok)result=wr_iot_saved_flash_compare(image,WR_IOT_NATIVE_NVRAM_SPACE,
                                        WR_IOT_NATIVE_NVRAM_SPACE,expected,length);
 done:
 if(fd>=0)close(fd);
 if(image){wr_iot_saved_wipe(image,WR_IOT_NATIVE_NVRAM_SPACE);free(image);}
 wr_iot_saved_wipe(&checked,sizeof(checked));
 wr_iot_saved_wipe(&request,sizeof(request));
 return result;
#else
 (void)expected;(void)length;return WR_IOT_FLASH_CONFIG_INVALID;
#endif
}
