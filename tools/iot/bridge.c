#include "bridge.h"
#include "subnet.h"
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <dirent.h>
#include <net/if.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <linux/sockios.h>
#define IOT_BRIDGE "br-iot"
#define IOT_OWNER "wr1200js-iot-v1"
static int owned(void) {
 char value[64];FILE *f;struct stat st;
 if(stat("/sys/class/net/br-iot/bridge",&st)||!S_ISDIR(st.st_mode))return 0;
 f=fopen("/sys/class/net/br-iot/ifalias","r");if(!f)return 0;
 if(!fgets(value,sizeof(value),f)){fclose(f);return 0;}fclose(f);
 value[strcspn(value,"\n")]=0;return !strcmp(value,IOT_OWNER);
}
static int empty_bridge(void) {
 DIR *d=opendir("/sys/class/net/br-iot/brif");struct dirent *e;int empty=1;
 if(!d)return 0;
 while((e=readdir(d)))if(strcmp(e->d_name,".")&&strcmp(e->d_name,"..")){empty=0;break;}
 closedir(d);return empty;
}
static int down_bridge(int fd) {
 struct ifreq req;memset(&req,0,sizeof(req));strcpy(req.ifr_name,IOT_BRIDGE);
 return ioctl(fd,SIOCGIFFLAGS,&req)==0&&!(req.ifr_flags&IFF_UP);
}
static int address(int fd,unsigned long operation,uint32_t value) {
 struct ifreq req;struct sockaddr_in *a;
 memset(&req,0,sizeof(req));strcpy(req.ifr_name,IOT_BRIDGE);
 a=(struct sockaddr_in *)&req.ifr_addr;a->sin_family=AF_INET;a->sin_addr.s_addr=htonl(value);
 return ioctl(fd,operation,&req)==0;
}
static int write_value(const char *path,const char *value) {
 FILE *f=fopen(path,"w");int result;if(!f)return 0;
 result=fputs(value,f)>=0;if(fclose(f))result=0;return result;
}
int wr_iot_bridge_prepare(const char *gateway,const char *mask,const char *start,const char *end,
 const struct wr_iot_range *reserved,size_t count) {
 struct wr_iot_subnet plan;int fd,created=0,ok=0;
 if(!wr_iot_subnet_plan(&plan,gateway,mask,start,end,reserved,count))return 0;
 fd=socket(AF_INET,SOCK_DGRAM,0);if(fd<0)return 0;
 if(if_nametoindex(IOT_BRIDGE)) {if(!owned())goto done;}
 else {
  if(ioctl(fd,SIOCBRADDBR,IOT_BRIDGE))goto done;
  created=1;
  if(!write_value("/sys/class/net/br-iot/ifalias",IOT_OWNER))goto done;
 }
 /* No automatic down: an active or attached bridge requires caller quiescence. */
 if(!down_bridge(fd)||!empty_bridge())goto done;
 if(!address(fd,SIOCSIFADDR,plan.gateway)||!address(fd,SIOCSIFNETMASK,plan.mask))goto done;
 if(access("/proc/sys/net/ipv6/conf/all/disable_ipv6",F_OK)==0&&
    !write_value("/proc/sys/net/ipv6/conf/br-iot/disable_ipv6","1"))goto done;
 ok=1;
 done:
 if(!ok&&created&&down_bridge(fd)&&empty_bridge())ioctl(fd,SIOCBRDELBR,IOT_BRIDGE);
 close(fd);return ok;
}
int wr_iot_bridge_remove(void) {
 int fd,ok;if(!if_nametoindex(IOT_BRIDGE))return 1;
 if(!owned())return 0;
 fd=socket(AF_INET,SOCK_DGRAM,0);if(fd<0)return 0;
 ok=down_bridge(fd)&&empty_bridge()&&ioctl(fd,SIOCBRDELBR,IOT_BRIDGE)==0;
 close(fd);return ok;
}

/* WR1200JS 2.4 GHz third-BSS candidate; actual driver creation still needs proof. */
#define IOT_BSS "ra2"
static int bss_down(int fd) {
 struct ifreq req;memset(&req,0,sizeof(req));strcpy(req.ifr_name,IOT_BSS);
 return ioctl(fd,SIOCGIFFLAGS,&req)==0&&!(req.ifr_flags&IFF_UP);
}
static int bss_master(void) {
 char path[256],*last;ssize_t n=readlink("/sys/class/net/ra2/master",path,sizeof(path)-1);
 if(n<0)return errno==ENOENT?0:-1;
 if((size_t)n>=sizeof(path)-1)return -1;
 path[n]=0;last=strrchr(path,'/');return !strcmp(last?last+1:path,IOT_BRIDGE)?1:-1;
}
static int membership(int fd,unsigned long operation) {
 struct ifreq req;unsigned int index=if_nametoindex(IOT_BSS);if(!index)return 0;
 memset(&req,0,sizeof(req));strcpy(req.ifr_name,IOT_BRIDGE);req.ifr_ifindex=(int)index;
 return ioctl(fd,operation,&req)==0;
}
int wr_iot_bss_set_down(void) {
 struct ifreq request;int fd,master,ok=0;
 if(!if_nametoindex(IOT_BSS))return 1;
 master=bss_master();
 if(master<0||(master==1&&!owned()))return 0;
 fd=socket(AF_INET,SOCK_DGRAM,0);if(fd<0)return 0;
 memset(&request,0,sizeof(request));strcpy(request.ifr_name,IOT_BSS);
 if(ioctl(fd,SIOCGIFFLAGS,&request))goto done;
 request.ifr_flags&=~IFF_UP;
 if(ioctl(fd,SIOCSIFFLAGS,&request))goto done;
 ok=bss_down(fd);
 done:close(fd);return ok;
}
int wr_iot_bridge_attach(void) {
 int fd,ok;if(!owned())return 0;
 fd=socket(AF_INET,SOCK_DGRAM,0);if(fd<0)return 0;
 ok=down_bridge(fd)&&empty_bridge()&&bss_down(fd)&&bss_master()==0&&membership(fd,SIOCBRADDIF);
 close(fd);return ok;
}
int wr_iot_bridge_detach(void) {
 int fd,master,ok;if(!if_nametoindex(IOT_BSS))return 1;
 master=bss_master();if(master==0)return 1;
 if(master<0||!owned())return 0;
 fd=socket(AF_INET,SOCK_DGRAM,0);if(fd<0)return 0;
 ok=bss_down(fd)&&membership(fd,SIOCBRDELIF);close(fd);return ok;
}

int wr_iot_bridge_is_owned(void) {return owned();}

/* Operate only on the owned bridge with no foreign members. This does not
 * establish firewall readiness; the activation controller must prove it first. */
int wr_iot_bridge_set_up(int enabled) {
 DIR *directory;struct dirent *entry;struct ifreq request;
 int fd,ok=0,members=0,foreign=0;
 if(enabled!=0&&enabled!=1)return 0;
 /* Recovery also runs after failures before bridge creation. An absent bridge
  * is already down; trying to bring an absent bridge up must still fail. */
 if(!if_nametoindex(IOT_BRIDGE))return !enabled;
 if(!owned())return 0;
 directory=opendir("/sys/class/net/br-iot/brif");if(!directory)return 0;
 while((entry=readdir(directory))) {
  if(!strcmp(entry->d_name,".")||!strcmp(entry->d_name,".."))continue;
  members++;
  if(strcmp(entry->d_name,IOT_BSS))foreign=1;
 }
 closedir(directory);
 if(foreign||(enabled&&members!=1))return 0;
 fd=socket(AF_INET,SOCK_DGRAM,0);if(fd<0)return 0;
 if(members&&(bss_master()!=1||!bss_down(fd)))goto done;
 memset(&request,0,sizeof(request));strcpy(request.ifr_name,IOT_BRIDGE);
 if(ioctl(fd,SIOCGIFFLAGS,&request))goto done;
 if(enabled)request.ifr_flags|=IFF_UP;
 else request.ifr_flags&=~IFF_UP;
 if(ioctl(fd,SIOCSIFFLAGS,&request))goto done;
 if(ioctl(fd,SIOCGIFFLAGS,&request))goto done;
 ok=!!(request.ifr_flags&IFF_UP)==enabled;
 done:close(fd);return ok;
}
