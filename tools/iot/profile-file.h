/* Caller serializes radio profile generation; temporary file is never activated early. */
#ifndef WR_IOT_PROFILE_FILE_H
#define WR_IOT_PROFILE_FILE_H
#include "profile-stream.h"
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#ifndef WR_IOT_MKSTEMP
#define WR_IOT_MKSTEMP mkstemp
#endif
#ifndef WR_IOT_FSYNC
#define WR_IOT_FSYNC fsync
#endif
#ifndef WR_IOT_RENAME
#define WR_IOT_RENAME rename
#endif
#ifndef WR_IOT_CLOSE
#define WR_IOT_CLOSE fclose
#endif
static int wr_iot_profile_replace(const char *path,const char *ssid,const char *password,int enabled) {
 FILE *input=NULL,*temporary=NULL;int in_fd=-1,out_fd=-1,committed=0,created=0;char *name=NULL;
 struct stat original,current;size_t n;
 if(!enabled)return 1;
 if(!path||!ssid||!password)return 0;
 n=strlen(path);if(n>4096)return 0;
 name=malloc(n+12);if(!name)return 0;
 memcpy(name,path,n);memcpy(name+n,".iot.XXXXXX",12);
 in_fd=open(path,O_RDONLY|O_NOFOLLOW);if(in_fd<0)goto done;
 if(fstat(in_fd,&original)||!S_ISREG(original.st_mode))goto done;
 input=fdopen(in_fd,"r");if(!input)goto done;in_fd=-1;
 out_fd=WR_IOT_MKSTEMP(name);if(out_fd<0)goto done;created=1;
 temporary=fdopen(out_fd,"w");if(!temporary)goto done;out_fd=-1;
 if(!wr_iot_profile_stream(input,temporary,ssid,password,1))goto done;
 if(fflush(temporary)||WR_IOT_FSYNC(fileno(temporary)))goto done;
 if(WR_IOT_CLOSE(temporary)){temporary=NULL;goto done;}temporary=NULL;
 /* Detect changes before commit; caller locking still covers the final rename window. */
 if(lstat(path,&current)||current.st_dev!=original.st_dev||current.st_ino!=original.st_ino||
    current.st_size!=original.st_size||current.st_mtime!=original.st_mtime||current.st_ctime!=original.st_ctime)goto done;
 if(WR_IOT_RENAME(name,path))goto done;
 committed=1;
 done:
 if(input)fclose(input);else if(in_fd>=0)close(in_fd);
 if(temporary)fclose(temporary);else if(out_fd>=0)close(out_fd);
 if(name){if(created&&!committed)unlink(name);free(name);}
 return committed;
}
#endif
