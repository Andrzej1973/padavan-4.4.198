#ifndef WR_USBIP_EXPORT_SETTINGS_H
#define WR_USBIP_EXPORT_SETTINGS_H
#include <sys/file.h>
#include "export-store.h"
#ifndef WR_USBIP_EXPORT_DIRECTORY
#define WR_USBIP_EXPORT_DIRECTORY "/etc/storage/usbip"
#endif
#ifndef WR_USBIP_LIFECYCLE_LOCK
#define WR_USBIP_LIFECYCLE_LOCK "/var/run/wr-usbip.lock"
#endif
enum wr_usbip_settings_state { WR_USBIP_SETTINGS_UNKNOWN=0,WR_USBIP_SETTINGS_READY=1,
 WR_USBIP_SETTINGS_EMPTY=2,WR_USBIP_SETTINGS_BUSY=3 };
static inline int wr_usbip_settings_lock(void)
{
 struct stat s;int fd=open(WR_USBIP_LIFECYCLE_LOCK,O_RDWR|O_CREAT|O_NOFOLLOW|O_NONBLOCK|O_CLOEXEC,0600);
 if(fd<0)return -1;
 if(fstat(fd,&s)||!wr_usbip_store_private_file(&s)){
  close(fd);return -1;
 }
 if(flock(fd,LOCK_EX|LOCK_NB)){
  int busy=errno==EWOULDBLOCK||errno==EAGAIN;close(fd);return busy?-2:-1;
 }
 return fd;
}
static inline enum wr_usbip_store_result wr_usbip_settings_save(
 const struct wr_usbip_export_rule rules[16])
{
 int fd;enum wr_usbip_store_result result;
 if(wr_usbip_export_validate(rules,16,NULL)!=WR_USBIP_EXPORT_OK)return WR_USBIP_STORE_REFUSED;
 fd=wr_usbip_settings_lock();if(fd<0)return WR_USBIP_STORE_REFUSED;
 if(mkdir(WR_USBIP_EXPORT_DIRECTORY,0700)&&errno!=EEXIST){close(fd);return WR_USBIP_STORE_REFUSED;}
 result=wr_usbip_export_save_locked(WR_USBIP_EXPORT_DIRECTORY,rules);
 close(fd);return result;
}
static inline enum wr_usbip_settings_state wr_usbip_settings_read(
 struct wr_usbip_export_rule out[16])
{
 int lock,dir;struct stat s;enum wr_usbip_settings_state result=WR_USBIP_SETTINGS_UNKNOWN;
 if(!out)return result;
 lock=wr_usbip_settings_lock();if(lock<0)return lock==-2?WR_USBIP_SETTINGS_BUSY:WR_USBIP_SETTINGS_UNKNOWN;
 dir=wr_usbip_store_directory(WR_USBIP_EXPORT_DIRECTORY);
 if(dir<0){
  if(errno==ENOENT)result=WR_USBIP_SETTINGS_EMPTY;
 }else{
  if(fstatat(dir,"exports.v1",&s,AT_SYMLINK_NOFOLLOW)){
   if(errno==ENOENT)result=WR_USBIP_SETTINGS_EMPTY;
  }else if(wr_usbip_export_load_locked(WR_USBIP_EXPORT_DIRECTORY,out))result=WR_USBIP_SETTINGS_READY;
  close(dir);
 }
 if(result==WR_USBIP_SETTINGS_EMPTY)memset(out,0,sizeof(*out)*16);
 close(lock);return result;
}
#endif
