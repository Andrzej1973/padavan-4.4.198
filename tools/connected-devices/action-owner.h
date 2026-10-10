#ifndef WR_ACTION_OWNER_H
#define WR_ACTION_OWNER_H
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <stdio.h>
#include <sys/types.h>
/* Linux proc stat comm may contain spaces and closing parentheses. The final
 * closing parenthesis ends comm; field 22 is starttime, not a wall clock. */
static inline int wr_action_birth_parse(const char *text,uint64_t *out){
 const char *p,*end;char *tail;unsigned long long value;unsigned field;
 if(!text||!out||!(p=strrchr(text,')'))||p[1]!=' ')return 0;
 p+=2;
 for(field=3;field<=22;field++){
  while(*p==' ')p++;
  end=p;while(*end&&*end!=' '&&*end!='\n')end++;
  if(end==p)return 0;
  if(field==22){
   const char *digit;for(digit=p;digit<end;digit++)if(*digit<'0'||*digit>'9')return 0;
   errno=0;value=strtoull(p,&tail,10);
   if(errno||tail!=end||!value)return 0;
   *out=(uint64_t)value;return 1;
  }
  if(!*end||*end=='\n')return 0;
  p=end+1;
 }
 return 0;
}
/* Match the retained exclusive flock, not a blocked waiter (->), POSIX
 * record lock or another process. Layout verified against pinned fs/locks.c. */
static inline int wr_action_lock_matches(const char *line,pid_t pid,
 unsigned device_major,unsigned device_minor,unsigned long long inode){
 unsigned long long id,actual_inode;unsigned maj,min;long owner;char kind[16],mode[16],access[16],start[16],finish[16],extra;
 if(!line||pid<=0)return 0;
 if(sscanf(line,"%llu: %15s %15s %15s %ld %x:%x:%llu %15s %15s %c",
 &id,kind,mode,access,&owner,&maj,&min,&actual_inode,start,finish,&extra)!=9)return 0;
 return !strcmp(kind,"FLOCK")&&!strcmp(mode,"ADVISORY")&&!strcmp(access,"WRITE")&&
 owner==(long)pid&&maj==device_major&&min==device_minor&&actual_inode==inode&&
 !strcmp(start,"0")&&!strcmp(finish,"EOF");
}
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <limits.h>
struct wr_action_owner {pid_t pid;uid_t uid;uint64_t birth;};
static inline int wr_action_read_small(const char *path,char *data,size_t capacity){
 int fd;ssize_t n;size_t used=0;
 fd=open(path,O_RDONLY|O_CLOEXEC|O_NOFOLLOW);if(fd<0)return 0;
 while(used<capacity-1){n=read(fd,data+used,capacity-1-used);if(n<0&&errno==EINTR)continue;if(n<0){close(fd);return 0;}if(!n)break;used+=(size_t)n;}
 if(used==capacity-1){char extra;n=read(fd,&extra,1);if(n!=0){close(fd);return 0;}}
 close(fd);data[used]=0;return used!=0;
}
/* Read-only verification; output is committed only after a repeated birth,
 * executable and retained lock-inode check. Fixed production paths are supplied
 * by the caller. Bounds: 4096-byte stat, 256 lock lines of at most 255 bytes. */
static inline int wr_action_owner_verify(const char *lock_path,const char *executable,
 const char *proc_root,uid_t expected_uid,struct wr_action_owner *out){
 struct stat locked,after,wanted,actual,process;struct wr_action_owner candidate;
 char text[4096],path[256],line[256],*tail;long pid;uint64_t birth;FILE *locks;unsigned count;int found=0;
 if(!out||!lock_path||!executable||!proc_root)return 0;
 if(lstat(lock_path,&locked)||!S_ISREG(locked.st_mode)||locked.st_uid!=expected_uid||locked.st_nlink!=1||(locked.st_mode&0777)!=0600)return 0;
 if(!wr_action_read_small(lock_path,text,32))return 0;
 errno=0;pid=strtol(text,&tail,10);
 if(errno||pid<=0||pid>INT_MAX||tail==text||strcmp(tail,"\n"))return 0;
 candidate.pid=(pid_t)pid;candidate.uid=expected_uid;
 if(stat(executable,&wanted)||!S_ISREG(wanted.st_mode)||wanted.st_uid!=expected_uid||(wanted.st_mode&022))return 0;
 if(snprintf(path,sizeof(path),"%s/%ld",proc_root,pid)>=(int)sizeof(path)||stat(path,&process)||process.st_uid!=expected_uid)return 0;
 if(snprintf(path,sizeof(path),"%s/%ld/stat",proc_root,pid)>=(int)sizeof(path)||!wr_action_read_small(path,text,sizeof(text))||!wr_action_birth_parse(text,&candidate.birth))return 0;
 if(snprintf(path,sizeof(path),"%s/%ld/exe",proc_root,pid)>=(int)sizeof(path)||stat(path,&actual)||actual.st_dev!=wanted.st_dev||actual.st_ino!=wanted.st_ino)return 0;
 if(snprintf(path,sizeof(path),"%s/locks",proc_root)>=(int)sizeof(path))return 0;
 locks=fopen(path,"r");if(!locks)return 0;
 for(count=0;count<256&&fgets(line,sizeof(line),locks);count++){
  if(!strchr(line,'\n')){fclose(locks);return 0;}
  if(wr_action_lock_matches(line,candidate.pid,major(locked.st_dev),minor(locked.st_dev),(unsigned long long)locked.st_ino))found=1;
 }
 if(ferror(locks)||(!feof(locks)&&fgetc(locks)!=EOF))found=0;
 fclose(locks);if(!found)return 0;
 if(lstat(lock_path,&after)||after.st_dev!=locked.st_dev||after.st_ino!=locked.st_ino||after.st_uid!=expected_uid||(after.st_mode&0777)!=0600)return 0;
 if(snprintf(path,sizeof(path),"%s/%ld/stat",proc_root,pid)>=(int)sizeof(path)||!wr_action_read_small(path,text,sizeof(text))||!wr_action_birth_parse(text,&birth)||birth!=candidate.birth)return 0;
 if(snprintf(path,sizeof(path),"%s/%ld/exe",proc_root,pid)>=(int)sizeof(path)||stat(path,&actual)||actual.st_dev!=wanted.st_dev||actual.st_ino!=wanted.st_ino)return 0;
 *out=candidate;return 1;
}
#endif
