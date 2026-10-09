/* Passive Linux socket inventory for one process; no configuration scripts run.
 * Caller must establish daemon identity before using this as readiness metadata. */
#ifndef WR_IOT_DNS_SOCKETS_H
#define WR_IOT_DNS_SOCKETS_H
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <dirent.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/stat.h>
struct wr_iot_dns_sockets {unsigned int dns_port;int dhcp_standard;unsigned int udp_ports[256],udp_count;};
static inline int wr_iot_dns_has_udp_port(const struct wr_iot_dns_sockets *state,unsigned int port){
 unsigned int i;if(!state||state->udp_count>256||!port||port>65535)return 0;
 for(i=0;i<state->udp_count;i++)if(state->udp_ports[i]==port)return 1;
 return 0;
}
struct wr_iot_dns_process_identity {unsigned long long start;dev_t device;ino_t executable;};
static inline int wr_iot_dns_start_time(const char *line,unsigned long long *out){
 const char *p;char *end;unsigned int field;unsigned long long start;
 if(!line||!out||(p=strrchr(line,')'))==NULL)return 0;
 p++;while(*p==' ')p++;
 for(field=3;field<22;field++){
  if(!*p)return 0;
  while(*p&&*p!=' ')p++;
  while(*p==' ')p++;
 }
 if(*p<'0'||*p>'9')return 0;
 errno=0;start=strtoull(p,&end,10);if(errno||end==p||(*end&&*end!=' '&&*end!='\n'))return 0;
 *out=start;return 1;
}
static inline int wr_iot_dns_process_identity(pid_t pid,struct wr_iot_dns_process_identity *out){
 char path[64],line[1024];struct stat executable,owner_namespace,caller_namespace;FILE *fp;int ok,missing;
 struct wr_iot_dns_process_identity identity;
 if(pid<=0||!out)return 0;
 snprintf(path,sizeof(path),"/proc/%ld/stat",(long)pid);fp=fopen(path,"r");if(!fp)return 0;
 ok=fgets(line,sizeof(line),fp)!=NULL&&strchr(line,'\n')&&wr_iot_dns_start_time(line,&identity.start);
 if(fclose(fp))ok=0;
 if(!ok)return 0;
 snprintf(path,sizeof(path),"/proc/%ld/exe",(long)pid);if(stat(path,&executable))return 0;
 identity.device=executable.st_dev;identity.executable=executable.st_ino;
 snprintf(path,sizeof(path),"/proc/%ld/ns/net",(long)pid);
 if(stat(path,&owner_namespace)){
  missing=errno==ENOENT;
  if(!missing||!stat("/proc/self/ns/net",&caller_namespace)||errno!=ENOENT)return 0;
 }else {
  if(stat("/proc/self/ns/net",&caller_namespace)||owner_namespace.st_dev!=caller_namespace.st_dev||owner_namespace.st_ino!=caller_namespace.st_ino)return 0;
 }
 *out=identity;return 1;
}
static inline int wr_iot_dns_same_process(const struct wr_iot_dns_process_identity *a,const struct wr_iot_dns_process_identity *b){
 return a->start==b->start&&a->device==b->device&&a->executable==b->executable;
}

static inline int wr_iot_dns_inode_owned(unsigned long long inode,const unsigned long long *owned,unsigned int count){
 unsigned int i;for(i=0;i<count;i++)if(inode==owned[i])return 1;return 0;
}
static inline int wr_iot_dns_socket_table(const char *path,int tcp,const unsigned long long *owned,unsigned int count,struct wr_iot_dns_sockets *state){
 FILE *fp;char line[512],local[80],remote[80];unsigned int number,flags,entries=0;unsigned long long inode;int ok=1;
 fp=fopen(path,"r");if(!fp)return errno==ENOENT;
 if(!fgets(line,sizeof(line),fp)){fclose(fp);return 0;}
 while(fgets(line,sizeof(line),fp)){
  char *colon,*end;unsigned long port;
  if(++entries>4096||(!strchr(line,'\n')&&!feof(fp))){ok=0;break;}
  if(sscanf(line," %u: %79s %79s %x %*s %*s %*s %*s %*s %llu",&number,local,remote,&flags,&inode)!=5){ok=0;break;}
  if(!wr_iot_dns_inode_owned(inode,owned,count))continue;
  colon=strrchr(local,':');if(!colon||!colon[1]){ok=0;break;}
  port=strtoul(colon+1,&end,16);if(*end||port>65535){ok=0;break;}
  if(tcp&&flags==10&&port){
   if(state->dns_port&&state->dns_port!=port){ok=0;break;}
   state->dns_port=(unsigned int)port;
  }
  if(!tcp&&port){
   if(!wr_iot_dns_has_udp_port(state,(unsigned int)port)){if(state->udp_count==256){ok=0;break;}state->udp_ports[state->udp_count++]=(unsigned int)port;}
   if(port==67)state->dhcp_standard=1;
  }
 }
 if(ferror(fp))ok=0;
 if(fclose(fp))ok=0;
 return ok;
}
static inline int wr_iot_dns_process_sockets(pid_t pid,struct wr_iot_dns_sockets *out){
 char path[64],link[512];unsigned long long owned[256];unsigned int count=0,entries=0;DIR *dir;struct dirent *entry;int ok=1;
 struct wr_iot_dns_sockets result={0};struct wr_iot_dns_process_identity before,after;
 if(pid<=0||!out||!wr_iot_dns_process_identity(pid,&before))return 0;
 if(snprintf(path,sizeof(path),"/proc/%ld/fd",(long)pid)<0)return 0;
 dir=opendir(path);if(!dir)return 0;
 errno=0;
 while((entry=readdir(dir))){
  ssize_t n;unsigned long long inode;int consumed=0;
  if(entry->d_name[0]=='.')continue;
  if(++entries>256){ok=0;break;}
  n=readlinkat(dirfd(dir),entry->d_name,link,sizeof(link)-1);
  if(n<0){ok=0;break;}if((size_t)n>=sizeof(link)-1){ok=0;break;}link[n]=0;
  if(sscanf(link,"socket:[%llu]%n",&inode,&consumed)==1&&consumed==(int)n){if(count==256){ok=0;break;}owned[count++]=inode;}
  errno=0;
 }
 if(errno)ok=0;
 if(closedir(dir))ok=0;
 if(!ok)return 0;
 if(!wr_iot_dns_socket_table("/proc/net/tcp",1,owned,count,&result)||
    !wr_iot_dns_socket_table("/proc/net/tcp6",1,owned,count,&result)||
    !wr_iot_dns_socket_table("/proc/net/udp",0,owned,count,&result))return 0;
 if(!wr_iot_dns_process_identity(pid,&after)||!wr_iot_dns_same_process(&before,&after))return 0;
 if(result.dns_port==67)result.dhcp_standard=0;
 *out=result;return 1;
}
/* Require the caller's trusted executable, not a process-name match alone.
 * Publish metadata only after executable and process identity remain stable. */
static inline int wr_iot_dns_daemon_sockets(pid_t pid,const char *executable,struct wr_iot_dns_sockets *out){
 struct stat expected,again;struct wr_iot_dns_process_identity before,after;
 struct wr_iot_dns_sockets result;
 if(!executable||!out||stat(executable,&expected)||!S_ISREG(expected.st_mode)||
    !wr_iot_dns_process_identity(pid,&before)||before.device!=expected.st_dev||before.executable!=expected.st_ino)return 0;
 if(!wr_iot_dns_process_sockets(pid,&result)||!wr_iot_dns_process_identity(pid,&after)||
    !wr_iot_dns_same_process(&before,&after)||stat(executable,&again)||
    again.st_dev!=expected.st_dev||again.st_ino!=expected.st_ino)return 0;
 *out=result;return 1;
}
/* Bounded process snapshot: only one matching executable in our net namespace.
 * Process names and pidfile contents are not accepted as identity evidence. */
static inline int wr_iot_dns_unique_daemon(const char *executable,pid_t *out){
 struct stat expected,again,actual;struct wr_iot_dns_process_identity identity;
 DIR *dir;struct dirent *entry;unsigned int entries=0;pid_t found=0;int ok=1;
 if(!executable||!out||stat(executable,&expected)||!S_ISREG(expected.st_mode))return 0;
 dir=opendir("/proc");if(!dir)return 0;
 errno=0;
 while((entry=readdir(dir))){
  char path[64],*end;long number;
  if(entry->d_name[0]<'0'||entry->d_name[0]>'9'){errno=0;continue;}
  if(++entries>4096){ok=0;break;}
  errno=0;number=strtol(entry->d_name,&end,10);
  if(errno||*end||number<=0||(long)(pid_t)number!=number){errno=0;continue;}
  snprintf(path,sizeof(path),"/proc/%ld/exe",number);
  if(!stat(path,&actual)&&actual.st_dev==expected.st_dev&&actual.st_ino==expected.st_ino&&
     wr_iot_dns_process_identity((pid_t)number,&identity)){
   if(identity.device!=expected.st_dev||identity.executable!=expected.st_ino){ok=0;break;}
   if(found){ok=0;break;}found=(pid_t)number;
  }
  errno=0;
 }
 if(errno)ok=0;
 if(closedir(dir))ok=0;
 if(!ok||!found||stat(executable,&again)||again.st_dev!=expected.st_dev||again.st_ino!=expected.st_ino||
    !wr_iot_dns_process_identity(found,&identity)||identity.device!=expected.st_dev||identity.executable!=expected.st_ino)return 0;
 *out=found;return 1;
}
static inline int wr_iot_dns_selected_sockets(const char *executable,struct wr_iot_dns_sockets *out){
 pid_t before,after;struct wr_iot_dns_sockets result;struct wr_iot_dns_process_identity first,last;
 if(!out||!wr_iot_dns_unique_daemon(executable,&before)||!wr_iot_dns_process_identity(before,&first)||!wr_iot_dns_daemon_sockets(before,executable,&result)||
    !wr_iot_dns_unique_daemon(executable,&after)||before!=after||!wr_iot_dns_process_identity(after,&last)||!wr_iot_dns_same_process(&first,&last))return 0;
 *out=result;return 1;
}

#endif
