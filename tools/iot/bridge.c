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
 char value[64];FILE *f;struct stat st;int ok;
 if(stat("/sys/class/net/br-iot/bridge",&st)||!S_ISDIR(st.st_mode))return 0;
 f=fopen("/sys/class/net/br-iot/ifalias","r");if(!f)return 0;
 if(!fgets(value,sizeof(value),f)){fclose(f);return 0;}
 /* A truncated/error read or trailing data is not an ownership receipt. */
 ok=!ferror(f)&&fgetc(f)==EOF&&!ferror(f);
 if(fclose(f))ok=0;
 value[strcspn(value,"\n")]=0;return ok&&!strcmp(value,IOT_OWNER);
}
static int empty_bridge(void) {
 DIR *d=opendir("/sys/class/net/br-iot/brif");struct dirent *e;int empty=1,failed;
 if(!d)return 0;
 errno=0;
 while((e=readdir(d)))if(strcmp(e->d_name,".")&&strcmp(e->d_name,"..")){empty=0;break;}
 failed=errno!=0;if(closedir(d))failed=1;
 return !failed&&empty;
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
static int address_matches(int fd,unsigned long operation,uint32_t value) {
 struct ifreq req;struct sockaddr_in *a;
 memset(&req,0,sizeof(req));strcpy(req.ifr_name,IOT_BRIDGE);
 if(ioctl(fd,operation,&req))return 0;
 a=(struct sockaddr_in *)&req.ifr_addr;
 return a->sin_family==AF_INET&&a->sin_addr.s_addr==htonl(value);
}
static int write_value(const char *path,const char *value) {
 FILE *f=fopen(path,"w");int result;if(!f)return 0;
 result=fputs(value,f)>=0;if(fclose(f))result=0;return result;
}
int wr_iot_bridge_address_matches(const char *gateway,const char *mask) {
 uint32_t g,m;int fd,ok;
 if(!wr_iot_ipv4(gateway,&g)||!wr_iot_ipv4(mask,&m)||!owned())return 0;
 fd=socket(AF_INET,SOCK_DGRAM,0);if(fd<0)return 0;
 ok=address_matches(fd,SIOCGIFADDR,g)&&address_matches(fd,SIOCGIFNETMASK,m)&&owned();
 if(close(fd))ok=0;
 return ok;
}
static int ipv6_disabled(void) {
 FILE *f;char value[16];int ok;
 /* No IPv6 sysctl tree is valid only when it is genuinely absent. Permission
  * and other lookup errors cannot stand in for disabled IPv6. */
 if(access("/proc/sys/net/ipv6/conf/all/disable_ipv6",F_OK))return errno==ENOENT;
 f=fopen("/proc/sys/net/ipv6/conf/br-iot/disable_ipv6","r");if(!f)return 0;
 ok=fgets(value,sizeof(value),f)!=NULL;
 if(ok)ok=(!strcmp(value,"1\n")||!strcmp(value,"1"))&&fgetc(f)==EOF&&!ferror(f);
 if(fclose(f))ok=0;
 return ok;
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
 ok=owned()&&down_bridge(fd)&&empty_bridge()&&ipv6_disabled()&&
    address_matches(fd,SIOCGIFADDR,plan.gateway)&&
    address_matches(fd,SIOCGIFNETMASK,plan.mask);
 done:
 /* A failed owner-marker write may leave a created resource. Retain that
  * uncertainty rather than deleting an object no longer provably owned. */
 if(!ok&&created&&owned()&&down_bridge(fd)&&empty_bridge())ioctl(fd,SIOCBRDELBR,IOT_BRIDGE);
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
int wr_iot_bss_is_down(void) {
 int fd,master,ok;
 if(!if_nametoindex(IOT_BSS))return 1;
 master=bss_master();
 if(master<0||(master==1&&!owned()))return 0;
 fd=socket(AF_INET,SOCK_DGRAM,0);if(fd<0)return 0;
 ok=bss_down(fd);
 if(close(fd))ok=0;
 return ok;
}
static int sole_bss_member(void);
int wr_iot_bridge_attach(void) {
 int fd,ok,master;if(!owned())return 0;
 fd=socket(AF_INET,SOCK_DGRAM,0);if(fd<0)return 0;
 master=bss_master();
 /* A prior attach can have succeeded before its final observation failed.
  * Adopt only the exact owned DOWN topology, never a foreign/extra member. */
 if(master==1)ok=down_bridge(fd)&&bss_down(fd)&&sole_bss_member();
 else ok=master==0&&down_bridge(fd)&&empty_bridge()&&bss_down(fd)&&membership(fd,SIOCBRADDIF);
 if(ok)ok=owned()&&down_bridge(fd)&&bss_down(fd)&&bss_master()==1&&sole_bss_member();
 if(close(fd))ok=0;
 return ok;
}
static int sole_bss_member(void) {
 DIR *directory;struct dirent *entry;int members=0,foreign=0,failed;
 directory=opendir("/sys/class/net/br-iot/brif");if(!directory)return 0;
 errno=0;
 while((entry=readdir(directory))) {
  if(!strcmp(entry->d_name,".")||!strcmp(entry->d_name,".."))continue;
  if(strcmp(entry->d_name,IOT_BSS))foreign=1;else members++;
 }
 failed=errno!=0;if(closedir(directory))failed=1;
 return !failed&&!foreign&&members==1;
}
int wr_iot_bss_is_active(void) {
 struct ifreq request;int fd,ok=0;
 if(!owned()||!ipv6_disabled()||bss_master()!=1||!sole_bss_member())return 0;
 fd=socket(AF_INET,SOCK_DGRAM,0);if(fd<0)return 0;
 memset(&request,0,sizeof(request));strcpy(request.ifr_name,IOT_BRIDGE);
 if(ioctl(fd,SIOCGIFFLAGS,&request)||!(request.ifr_flags&IFF_UP))goto done;
 memset(&request,0,sizeof(request));strcpy(request.ifr_name,IOT_BSS);
 if(ioctl(fd,SIOCGIFFLAGS,&request)||!(request.ifr_flags&IFF_UP))goto done;
 ok=owned()&&ipv6_disabled()&&bss_master()==1&&sole_bss_member();
 done:if(close(fd))ok=0;return ok;
}
int wr_iot_bss_set_up(void) {
 struct ifreq request;int fd,ok=0;
 if(!owned()||!ipv6_disabled()||bss_master()!=1||!sole_bss_member())return 0;
 fd=socket(AF_INET,SOCK_DGRAM,0);if(fd<0)return 0;
 memset(&request,0,sizeof(request));strcpy(request.ifr_name,IOT_BRIDGE);
 if(ioctl(fd,SIOCGIFFLAGS,&request)||!(request.ifr_flags&IFF_UP))goto done;
 memset(&request,0,sizeof(request));strcpy(request.ifr_name,IOT_BSS);
 if(ioctl(fd,SIOCGIFFLAGS,&request))goto done;
 request.ifr_flags|=IFF_UP;
 if(ioctl(fd,SIOCSIFFLAGS,&request)||ioctl(fd,SIOCGIFFLAGS,&request))goto done;
 ok=!!(request.ifr_flags&IFF_UP)&&owned()&&ipv6_disabled()&&bss_master()==1&&sole_bss_member();
 done:close(fd);return ok;
}
int wr_iot_bridge_detach(void) {
 int fd,master,ok;if(!if_nametoindex(IOT_BSS))return 1;
 master=bss_master();if(master==0)return 1;
 if(master<0||!owned())return 0;
 fd=socket(AF_INET,SOCK_DGRAM,0);if(fd<0)return 0;
 ok=bss_down(fd)&&membership(fd,SIOCBRDELIF);
 if(ok)ok=owned()&&bss_down(fd)&&bss_master()==0;
 if(close(fd))ok=0;
 return ok;
}

int wr_iot_bridge_is_owned(void) {return owned();}

/* Operate only on the owned bridge with no foreign members. This does not
 * establish firewall readiness; the activation controller must prove it first. */
int wr_iot_bridge_set_up(int enabled) {
 DIR *directory;struct dirent *entry;struct ifreq request;
 int fd,ok=0,members=0,foreign=0,failed;
 if(enabled!=0&&enabled!=1)return 0;
 /* Recovery also runs after failures before bridge creation. An absent bridge
  * is already down; trying to bring an absent bridge up must still fail. */
 if(!if_nametoindex(IOT_BRIDGE))return !enabled;
 if(!owned())return 0;
 directory=opendir("/sys/class/net/br-iot/brif");if(!directory)return 0;
 errno=0;
 while((entry=readdir(directory))) {
  if(!strcmp(entry->d_name,".")||!strcmp(entry->d_name,".."))continue;
  members++;
  if(strcmp(entry->d_name,IOT_BSS))foreign=1;
 }
 failed=errno!=0;if(closedir(directory))failed=1;
 if(failed||foreign||(enabled&&members!=1))return 0;
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
