#!/usr/bin/env python3
"""Actual native adapters with real snapshot parser and syscall actors."""
from pathlib import Path
import subprocess
import tempfile
here=Path(__file__).resolve().parent
shared=here.parent/'band-steering'
source=r'''
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdarg.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <sys/ioctl.h>
#include <assert.h>
#include <string.h>
#include "bcmnvram.h"
#include "native-flash-wire.h"
static pid_t actor_pid=123;
static pid_t mock_getpid(void){return actor_pid;}
static int expected_flags;
static int opens,stats,ioctls,closes,open_error,stat_error,regular,wrong_major,ioctl_error,close_error;
static int dump_error,dumps;static const char *policy="0",*record="expected";
int nvram_getall(char *out,int capacity,int temp){
 size_t at=0,n;assert(capacity>100&&temp==1);dumps++;if(dump_error)return -1;
 memset(out,0,capacity);n=strlen("wr_iot_config_v1=");memcpy(out,"wr_iot_config_v1=",n);at=n;
 n=strlen(record);memcpy(out+at,record,n);at+=n+1;
 if(policy){n=strlen("nvram_manual=");memcpy(out+at,"nvram_manual=",n);at+=n;
 n=strlen(policy);memcpy(out+at,policy,n);}
 return 0;
}
static int mock_open(const char *p,int flags,...){assert(!strcmp(p,"/dev/nvram")&&flags==(O_RDWR|O_CLOEXEC|O_NOFOLLOW));opens++;return open_error?-1:17;}
static int mock_fstat(int fd,struct stat *s){assert(fd==17);stats++;memset(s,0,sizeof(*s));s->st_mode=regular?S_IFREG:S_IFCHR;s->st_rdev=makedev(wrong_major?1:228,0);return stat_error;}
static int mock_ioctl(int fd,unsigned long req,...){va_list ap;struct wr_nvram_save_profile *q;
 assert(fd==17&&req==WR_NVRAM_IOCTL_SAVE_PROFILE);
 va_start(ap,req);q=va_arg(ap,struct wr_nvram_save_profile*);va_end(ap);
 assert(q->size==400&&q->version==1&&q->flags==(unsigned int)expected_flags&&q->record_length==8&&!strcmp(q->record,"expected"));
 ioctls++;return ioctl_error;}
static int mock_close(int fd){assert(fd==17);closes++;return close_error;}
#define getpid mock_getpid
#define open mock_open
#define fstat mock_fstat
#define ioctl mock_ioctl
#define close mock_close
#include "flash-save-native.c"
static void reset(void){opens=stats=ioctls=closes=open_error=stat_error=regular=wrong_major=ioctl_error=close_error=0;actor_pid=123;}
int main(void){
 int manual=7,i;
 assert(wr_iot_flash_save_snapshot("expected",&manual)&&manual==0);
 policy="1";assert(wr_iot_flash_save_snapshot("expected",&manual)&&manual==1);
 policy=NULL;assert(wr_iot_flash_save_snapshot("expected",&manual)&&manual==0);
 policy="";assert(wr_iot_flash_save_snapshot("expected",&manual)&&manual==0);
 policy="invalid";manual=7;assert(!wr_iot_flash_save_snapshot("expected",&manual)&&manual==7);
 policy="0";record="foreign";assert(!wr_iot_flash_save_snapshot("expected",&manual)&&manual==7);
 record="expected";dump_error=1;assert(!wr_iot_flash_save_snapshot("expected",&manual)&&manual==7);dump_error=0;
 actor_pid=1;dumps=0;assert(!wr_iot_flash_save_snapshot("expected",&manual)&&!dumps);
 reset();assert(!wr_iot_flash_save_commit_once("expected",8,WR_IOT_FLASH_SAVE_AUTO)&&opens==1&&stats==1&&ioctls==1&&closes==1);
 reset();expected_flags=1;assert(!wr_iot_flash_save_commit_once("expected",8,WR_IOT_FLASH_SAVE_EXPLICIT)&&ioctls==1);expected_flags=0;
 reset();actor_pid=1;assert(wr_iot_flash_save_commit_once("expected",8,WR_IOT_FLASH_SAVE_AUTO)==-1&&!opens);
 for(i=0;i<6;i++){
 reset();switch(i){case 0:open_error=1;break;case 1:stat_error=-1;break;
 case 2:regular=1;break;case 3:wrong_major=1;break;case 4:ioctl_error=-1;break;case 5:close_error=-1;break;}
 assert(wr_iot_flash_save_commit_once("expected",8,WR_IOT_FLASH_SAVE_AUTO)==-1&&opens==1&&ioctls<=1&&closes==(!open_error));
 }
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-flash-native-') as directory:
 root=Path(directory);(root/'rc.h').write_text('int nvram_getall(char *,int,int);\n')
 (root/'bcmnvram.h').write_bytes((here/'fixtures/config-bcmnvram.h').read_bytes())
 (root/'wr-band-settings-snapshot.h').write_bytes((shared/'settings-snapshot.h').read_bytes())
 cfile=root/'check.c';binary=root/'check';cfile.write_text(source)
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2',
 '-fsanitize=address,undefined','-fno-pie','-no-pie','-DWR_IOT_NATIVE_FLASH_READBACK_PREPARED=1',
 '-DWR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED=1','-DWR_IOT_NATIVE_NVRAM_SPACE=61440',
 '-I'+str(root),'-I'+str(here),'-I'+str(shared),str(cfile),str(shared/'settings-snapshot.c'),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=15)
print('PASS actual native save adapters + real snapshot parser: manual policy/record/error/PID1 checks and fixed once-only COMMIT syscall/error handling; no device I/O')
