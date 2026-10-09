/* Caller holds the service transaction lock; paths are trusted fixed service paths. */
#ifndef WR_IOT_SAVED_FILE_H
#define WR_IOT_SAVED_FILE_H
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#define WR_IOT_SAVED_LIMIT (256U*1024U)
struct wr_iot_saved_file {unsigned char *data;size_t size;int existed;struct stat metadata;};
static inline void wr_iot_saved_release(struct wr_iot_saved_file *file){
 if(file){if(file->data){memset(file->data,0,file->size);free(file->data);}memset(file,0,sizeof(*file));}
}
/* Output must be zero initialized. Read-only capture, untouched on failure. */
static inline int wr_iot_saved_capture(struct wr_iot_saved_file *out,const char *path){
 struct wr_iot_saved_file candidate;struct stat after;int fd;size_t used=0;unsigned char extra;
 if(!out||out->data||!path||!*path)return 0;
 memset(&candidate,0,sizeof(candidate));fd=open(path,O_RDONLY|O_NOFOLLOW|O_NONBLOCK);
 if(fd<0){if(errno!=ENOENT)return 0;*out=candidate;return 1;}
 if(fstat(fd,&candidate.metadata)||!S_ISREG(candidate.metadata.st_mode)||candidate.metadata.st_size<0||
    (unsigned long)candidate.metadata.st_size>WR_IOT_SAVED_LIMIT)goto fail;
 candidate.existed=1;candidate.size=(size_t)candidate.metadata.st_size;
 candidate.data=malloc(candidate.size?candidate.size:1);if(!candidate.data)goto fail;
 while(used<candidate.size){
  ssize_t n=read(fd,candidate.data+used,candidate.size-used);
  if(n<0&&errno==EINTR)continue;
  if(n<=0)goto fail;
  used+=(size_t)n;
 }
 if(read(fd,&extra,1)!=0||fstat(fd,&after)||after.st_dev!=candidate.metadata.st_dev||
    after.st_ino!=candidate.metadata.st_ino||after.st_size!=candidate.metadata.st_size||
    after.st_mtime!=candidate.metadata.st_mtime||after.st_ctime!=candidate.metadata.st_ctime)goto fail;
 if(close(fd)){wr_iot_saved_release(&candidate);return 0;}
 *out=candidate;return 1;
fail:close(fd);wr_iot_saved_release(&candidate);return 0;
}
#endif
