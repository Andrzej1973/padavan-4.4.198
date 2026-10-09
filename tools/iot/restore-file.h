/* Caller serializes all writers and records the generated file identity after its own writes. */
#ifndef WR_IOT_RESTORE_FILE_H
#define WR_IOT_RESTORE_FILE_H
#include "saved-file.h"
#include <stdio.h>
#ifndef WR_IOT_RESTORE_MKSTEMP
#define WR_IOT_RESTORE_MKSTEMP mkstemp
#endif
#ifndef WR_IOT_RESTORE_WRITE
#define WR_IOT_RESTORE_WRITE write
#endif
#ifndef WR_IOT_RESTORE_FSYNC
#define WR_IOT_RESTORE_FSYNC fsync
#endif
#ifndef WR_IOT_RESTORE_CLOSE
#define WR_IOT_RESTORE_CLOSE close
#endif
#ifndef WR_IOT_RESTORE_RENAME
#define WR_IOT_RESTORE_RENAME rename
#endif
struct wr_iot_generated_file {int existed;struct stat metadata;};
static inline int wr_iot_generated_capture(struct wr_iot_generated_file *out,const char *path){
 struct wr_iot_generated_file candidate;memset(&candidate,0,sizeof(candidate));
 if(!out||!path)return 0;
 if(lstat(path,&candidate.metadata)){if(errno!=ENOENT)return 0;}else{
  if(!S_ISREG(candidate.metadata.st_mode))return 0;
  candidate.existed=1;
 }
 *out=candidate;return 1;
}
static inline int wr_iot_generated_matches(const struct wr_iot_generated_file *expected,const char *path){
 struct wr_iot_generated_file current;
 if(!expected||!wr_iot_generated_capture(&current,path)||current.existed!=expected->existed)return 0;
 return !current.existed||(current.metadata.st_dev==expected->metadata.st_dev&&
 current.metadata.st_ino==expected->metadata.st_ino&&current.metadata.st_size==expected->metadata.st_size&&
 current.metadata.st_mtime==expected->metadata.st_mtime&&current.metadata.st_ctime==expected->metadata.st_ctime&&
 current.metadata.st_mode==expected->metadata.st_mode&&current.metadata.st_uid==expected->metadata.st_uid&&
 current.metadata.st_gid==expected->metadata.st_gid);
}
static inline int wr_iot_saved_restore(const struct wr_iot_saved_file *saved,const struct wr_iot_generated_file *expected,const char *path){
 char candidate[512];int fd,ok=0,n;size_t used=0;
 if(!saved||!path||!*path||saved->size>WR_IOT_SAVED_LIMIT||
    (saved->existed&&(!saved->data||!S_ISREG(saved->metadata.st_mode)))||
    !wr_iot_generated_matches(expected,path))return 0;
 if(!saved->existed)return !expected->existed||unlink(path)==0;
 n=snprintf(candidate,sizeof(candidate),"%s.iot-restore.XXXXXX",path);
 if(n<0||(size_t)n>=sizeof(candidate))return 0;
 fd=WR_IOT_RESTORE_MKSTEMP(candidate);if(fd<0)return 0;
 while(used<saved->size){ssize_t written=WR_IOT_RESTORE_WRITE(fd,saved->data+used,saved->size-used);
  if(written<0&&errno==EINTR)continue;
  if(written<=0)goto done;
  used+=(size_t)written;
 }
 if(fchown(fd,saved->metadata.st_uid,saved->metadata.st_gid)||
    fchmod(fd,saved->metadata.st_mode&0777)||WR_IOT_RESTORE_FSYNC(fd))goto done;
 if(WR_IOT_RESTORE_CLOSE(fd)){fd=-1;goto done;}fd=-1;
 if(!wr_iot_generated_matches(expected,path)||WR_IOT_RESTORE_RENAME(candidate,path))goto done;
 ok=1;
done:if(fd>=0)WR_IOT_RESTORE_CLOSE(fd);if(!ok)unlink(candidate);return ok;
}
#endif
