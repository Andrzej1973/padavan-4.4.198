#!/usr/bin/env python3
"""Exercise actual read-only client with native syscall actors; no device I/O."""
from pathlib import Path
import subprocess
import tempfile

here=Path(__file__).resolve().parent
fields=[b'0',b'IoT test',b'password123',b'192.168.50.1',b'255.255.255.0',b'192.168.50.20',b'192.168.50.200']
record='WR-IOT-CONFIG-1:'+':'.join(v.hex() for v in fields)
prefix=r'''
#include <stdint.h>
#include <stdlib.h>
#include <stdarg.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <sys/ioctl.h>
#include <assert.h>
#include <string.h>
#include "bcmnvram.h"
#include "native-flash-reader.h"
#include "native-flash-wire.h"
#if WR_IOT_NATIVE_FLASH_READBACK_PREPARED
static unsigned char fixture[61440];
static int open_error,stat_error,regular,wrong_major,alloc_error,ioctl_result,close_error;
static int opens,stats,allocs,ioctls,closes,frees;
static int mock_open(const char *path,int flags,...) {
 assert(!strcmp(path,"/dev/nvram"));assert(flags==(O_RDONLY|O_CLOEXEC|O_NOFOLLOW));
 opens++;return open_error?-1:17;
}
static int mock_fstat(int fd,struct stat *st) {
 assert(fd==17);stats++;memset(st,0,sizeof(*st));
 st->st_mode=regular?S_IFREG:S_IFCHR;st->st_rdev=makedev(wrong_major?1:228,0);return stat_error;
}
static void *mock_malloc(size_t n){assert(n==61440);allocs++;return alloc_error?NULL:calloc(1,n);}
static void mock_free(void *p){size_t i;for(i=0;i<61440;i++)assert(!((unsigned char*)p)[i]);frees++;free(p);}
static int mock_ioctl(int fd,unsigned long request,...) {
 va_list ap;anvram_ioctl_t *q;assert(fd==17&&request==WR_NVRAM_IOCTL_READ_FLASH);
 va_start(ap,request);q=va_arg(ap,anvram_ioctl_t*);va_end(ap);
 assert(q->size==sizeof(*q)&&!q->is_temp&&!q->len_param&&!q->param&&q->len_value==61440);
 ioctls++;memcpy(q->value,fixture,61440);return ioctl_result;
}
static int mock_close(int fd){assert(fd==17);closes++;return close_error;}
#define open mock_open
#define fstat mock_fstat
#define malloc mock_malloc
#define free mock_free
#define ioctl mock_ioctl
#define close mock_close
#endif
#include "native-flash-reader.c"
#undef open
#undef fstat
#undef malloc
#undef free
#undef ioctl
#undef close
'''
suffix=r'''
static const char expected[]="RECORD";
#if WR_IOT_NATIVE_FLASH_READBACK_PREPARED
static void reset(void){
 open_error=stat_error=regular=wrong_major=alloc_error=ioctl_result=close_error=0;
 opens=stats=allocs=ioctls=closes=frees=0;
}
static void make_image(const char *record){
 size_t n,i;unsigned char crc=255;
 memset(fixture,0,sizeof(fixture));
 strcpy((char*)fixture+20,"wr_iot_config_v1=");strcat((char*)fixture+20,record);
 n=(20+strlen((char*)fixture+20)+2+3)&~(size_t)3;
 fixture[0]=0x46;fixture[1]=0x4c;fixture[2]=0x53;fixture[3]=0x48;
 fixture[4]=n&255;fixture[5]=(n>>8)&255;fixture[9]=1;
 for(i=9;i<n;i++)crc=wr_iot_flash_crc(crc,fixture[i]);
 fixture[8]=crc;
}
#endif
int main(void){
#if WR_IOT_NATIVE_FLASH_READBACK_PREPARED
 int i;make_image(expected);reset();
 assert(wr_iot_native_flash_compare(expected,strlen(expected))==WR_IOT_FLASH_CONFIG_MATCH);
 assert(opens==1&&stats==1&&allocs==1&&ioctls==1&&closes==1&&frees==1);
 for(i=0;i<8;i++){
  reset();switch(i){case 0:open_error=1;break;case 1:stat_error=-1;break;
   case 2:regular=1;break;case 3:wrong_major=1;break;case 4:alloc_error=1;break;
   case 5:ioctl_result=-1;break;case 6:ioctl_result=1;break;case 7:close_error=-1;break;}
  assert(wr_iot_native_flash_compare(expected,strlen(expected))==WR_IOT_FLASH_CONFIG_INVALID);
  assert(opens==1&&ioctls<=1&&closes==(!open_error));
  assert(frees==((allocs&&!alloc_error)?1:0));
 }
 reset();assert(wr_iot_native_flash_compare("bad",3)==WR_IOT_FLASH_CONFIG_INVALID&&!opens);
 reset();fixture[21]^=1;assert(wr_iot_native_flash_compare(expected,strlen(expected))==WR_IOT_FLASH_CONFIG_INVALID&&frees==1);
#else
 assert(wr_iot_native_flash_compare(expected,strlen(expected))==WR_IOT_FLASH_CONFIG_INVALID);
#endif
 return 0;
}
'''.replace('RECORD',record)
with tempfile.TemporaryDirectory(prefix='wr-flash-reader-') as directory:
    root=Path(directory)
    (root/'bcmnvram.h').write_bytes((here/'fixtures/config-bcmnvram.h').read_bytes())
    source=root/'check.c';source.write_text(prefix+suffix)
    for enabled in (0,1):
        binary=root/('check'+str(enabled))
        subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2',
                        '-fsanitize=address,undefined','-fno-pie','-no-pie',
                        '-DWR_IOT_NATIVE_FLASH_READBACK_PREPARED='+str(enabled),
                        '-DWR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED=1',
                        '-DWR_IOT_NATIVE_NVRAM_SPACE=61440','-I'+str(root),'-I'+str(here),
                        str(source),'-o',str(binary)],check=True)
        subprocess.run([str(binary)],check=True,timeout=15)
print('PASS actual client capability0/1: fixed nofollow device, major/type validation, once-only ioctl, discard all error/close/corrupt buffers, full wipe/free; syscall actors only')
