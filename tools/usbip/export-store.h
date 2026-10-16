#ifndef WR_USBIP_EXPORT_STORE_H
#define WR_USBIP_EXPORT_STORE_H
/* Caller holds /var/run/wr-usbip.lock throughout. No MTD/storage-save call.
 * A renamed file is visible atomically; power-loss durability is separate. */
#include <errno.h>
#include <fcntl.h>
#include <stdlib.h>
#include <sys/stat.h>
#include <unistd.h>
#include "export-codec.h"
enum wr_usbip_store_result { WR_USBIP_STORE_REFUSED=0,WR_USBIP_STORE_SAVED=1,WR_USBIP_STORE_UNCONFIRMED=2 };
static inline int wr_usbip_store_private_file(const struct stat *s)
{
 return S_ISREG(s->st_mode)&&s->st_uid==geteuid()&&s->st_nlink==1&&!(s->st_mode&077);
}
static inline int wr_usbip_store_directory(const char *directory)
{
 struct stat s;int fd=open(directory,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);
 if(fd<0)return -1;
 if(fstat(fd,&s)){int error=errno;close(fd);errno=error;return -1;}
 if(s.st_uid!=geteuid()||(s.st_mode&077)){close(fd);errno=EACCES;return -1;}
 return fd;
}
static inline enum wr_usbip_store_result wr_usbip_export_save_locked(const char *directory,
 const struct wr_usbip_export_rule *rules)
{
 char *text=NULL,temp[64];struct stat s;int dir=-1,fd=-1;size_t length,offset=0;
 enum wr_usbip_store_result result=WR_USBIP_STORE_REFUSED;
 if(!directory||!rules)return result;
 text=malloc(WR_USBIP_EXPORT_TEXT_MAX);if(!text)return result;
 if(!wr_usbip_export_encode(rules,text,WR_USBIP_EXPORT_TEXT_MAX))goto done;
 length=strlen(text);dir=wr_usbip_store_directory(directory);if(dir<0)goto done;
 if(fstatat(dir,"exports.v1",&s,AT_SYMLINK_NOFOLLOW)==0){
  if(!wr_usbip_store_private_file(&s))goto done;
 }else if(errno!=ENOENT)goto done;
 snprintf(temp,sizeof(temp),"exports.tmp.%ld",(long)getpid());
 fd=openat(dir,temp,O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);
 if(fd<0)goto done;
 while(offset<length){
  ssize_t n=write(fd,text+offset,length-offset);
  if(n<0&&errno==EINTR)continue;
  if(n<=0)goto cleanup;
  offset+=(size_t)n;
 }
 if(fsync(fd))goto cleanup;
 if(close(fd)){fd=-1;goto cleanup;}fd=-1;
 if(renameat(dir,temp,dir,"exports.v1"))goto cleanup;
 result=fsync(dir)==0?WR_USBIP_STORE_SAVED:WR_USBIP_STORE_UNCONFIRMED;
 goto done;
cleanup:
 if(fd>=0){close(fd);fd=-1;}
 unlinkat(dir,temp,0);
done:
 if(dir>=0)close(dir);
 free(text);return result;
}
static inline int wr_usbip_export_load_locked(const char *directory,
 struct wr_usbip_export_rule out[16])
{
 char *text;struct stat s;int dir,fd,result=0;size_t used=0;
 if(!directory||!out)return 0;
 dir=wr_usbip_store_directory(directory);if(dir<0)return 0;
 fd=openat(dir,"exports.v1",O_RDONLY|O_NONBLOCK|O_NOFOLLOW|O_CLOEXEC);close(dir);
 if(fd<0)return 0;
 if(fstat(fd,&s)||!wr_usbip_store_private_file(&s)||s.st_size<=0||s.st_size>=WR_USBIP_EXPORT_TEXT_MAX){close(fd);return 0;}
 text=malloc(WR_USBIP_EXPORT_TEXT_MAX);if(!text){close(fd);return 0;}
 while(used<WR_USBIP_EXPORT_TEXT_MAX){
  ssize_t n=read(fd,text+used,WR_USBIP_EXPORT_TEXT_MAX-used);
  if(n<0&&errno==EINTR)continue;
  if(n<0)goto done;
  if(!n){result=wr_usbip_export_decode(text,used,out);break;}
  used+=(size_t)n;
 }
done:
 close(fd);free(text);return result;
}
#endif
