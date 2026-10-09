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
struct wr_iot_dns_sockets {unsigned int dns_port;int dhcp_standard;};
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
  if(!tcp&&port==67)state->dhcp_standard=1;
 }
 if(ferror(fp))ok=0;
 if(fclose(fp))ok=0;
 return ok;
}
static inline int wr_iot_dns_process_sockets(pid_t pid,struct wr_iot_dns_sockets *out){
 char path[64],link[512];unsigned long long owned[256];unsigned int count=0,entries=0;DIR *dir;struct dirent *entry;int ok=1;
 struct wr_iot_dns_sockets result={0,0};struct wr_iot_dns_process_identity before,after;
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
#endif
