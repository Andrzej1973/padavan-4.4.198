/* Compatible with pinned file_lock(): POSIX whole-file fcntl locks.
 * Nonblocking acquisition; fixed production paths belong to the HTTP caller. */
#ifndef WR_DEVICE_SOURCE_COLLECTOR_H
#define WR_DEVICE_SOURCE_COLLECTOR_H
#include "networkmap.h"
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
struct wr_device_source_paths {const char *source,*lock;};
static inline int wr_device_networkmap_collect(struct wr_device_snapshot *out,void *context){
 const struct wr_device_source_paths *paths=(const struct wr_device_source_paths *)context;
 struct wr_device_snapshot candidate;struct stat locked,before,after,current;struct flock lock;
 int fd=-1,guard=-1,ok=0;FILE *fp=NULL;
 if(!out||!paths||!paths->source||!paths->lock)return 0;
 guard=open(paths->lock,O_CREAT|O_RDWR|O_NOFOLLOW|O_CLOEXEC,0666);if(guard<0)return 0;
 if(fstat(guard,&locked)||!S_ISREG(locked.st_mode)||lstat(paths->lock,&current)||current.st_dev!=locked.st_dev||current.st_ino!=locked.st_ino)goto done;
 memset(&lock,0,sizeof(lock));lock.l_type=F_WRLCK;lock.l_whence=SEEK_SET;
 if(fcntl(guard,F_SETLK,&lock)<0)goto done;
 fd=open(paths->source,O_RDONLY|O_NONBLOCK|O_NOFOLLOW|O_CLOEXEC);if(fd<0)goto done;
 if(fstat(fd,&before)||!S_ISREG(before.st_mode))goto done;
 fp=fdopen(fd,"r");if(!fp)goto done;fd=-1;
 if(!wr_device_networkmap_read(fp,&candidate)||fstat(fileno(fp),&after)||lstat(paths->source,&current))goto done;
 if(!S_ISREG(current.st_mode)||before.st_dev!=after.st_dev||before.st_ino!=after.st_ino||before.st_size!=after.st_size||
    before.st_mtime!=after.st_mtime||before.st_ctime!=after.st_ctime||current.st_dev!=after.st_dev||current.st_ino!=after.st_ino)goto done;
 if(lstat(paths->lock,&current)||current.st_dev!=locked.st_dev||current.st_ino!=locked.st_ino)goto done;
 if(fclose(fp)){fp=NULL;goto done;}fp=NULL;ok=1;
 done:
 if(fp&&fclose(fp))ok=0;
 if(fd>=0&&close(fd))ok=0;
 /* Do not truncate/write the upstream lock's PID metadata. Closing releases our lock. */
 if(close(guard))ok=0;
 if(ok)*out=candidate;
 return ok;
}
#endif
