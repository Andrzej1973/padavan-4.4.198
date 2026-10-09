/* Only protects writers that participate in this lock; caller audits all service entry points. */
#ifndef WR_IOT_SERVICE_LOCK_H
#define WR_IOT_SERVICE_LOCK_H
#include <sys/file.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
struct wr_iot_service_lock {int fd;};
static inline int wr_iot_service_lock_valid(const struct wr_iot_service_lock *lock,const char *path){
 struct stat held,named;
 if(!lock||lock->fd<0||!path||fstat(lock->fd,&held)||lstat(path,&named))return 0;
 return S_ISREG(held.st_mode)&&S_ISREG(named.st_mode)&&held.st_nlink==1&&
 held.st_uid==geteuid()&&!(held.st_mode&0077)&&held.st_dev==named.st_dev&&held.st_ino==named.st_ino;
}
static inline int wr_iot_service_lock_take(struct wr_iot_service_lock *out,const char *path){
 struct wr_iot_service_lock candidate;
 if(!out||out->fd!=-1||!path||!*path)return 0;
 candidate.fd=open(path,O_RDWR|O_CREAT|O_NOFOLLOW|O_NONBLOCK|O_CLOEXEC,0600);
 if(candidate.fd<0)return 0;
 if(!wr_iot_service_lock_valid(&candidate,path)||flock(candidate.fd,LOCK_EX|LOCK_NB)||
    !wr_iot_service_lock_valid(&candidate,path)){close(candidate.fd);return 0;}
 *out=candidate;return 1;
}
/* Do not unlink: waiters and future users must share one persistent inode. */
static inline void wr_iot_service_lock_release(struct wr_iot_service_lock *lock){
 if(lock&&lock->fd>=0){close(lock->fd);lock->fd=-1;}
}
#endif
