#define _GNU_SOURCE
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <linux/sockios.h>
#include <net/if.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include "restart-main-bridge.h"
#include "service-guard.h"
static int master(void)
{
 char path[256];ssize_t n=readlink("/sys/class/net/ra0/master",path,sizeof(path)-1);
 if(n<0)return errno==ENOENT?0:-1;
 if((size_t)n>=sizeof(path)-1)return -1;
 path[n]=0;
 /* Kernel sysfs master link target, compared with exact pinned bridge name. */
 {char *last=strrchr(path,'/');return last&&!strcmp(last+1,"br0")?1:-1;}
}
static int guard(void)
{int fd=wr_iot_service_guard_dup();return fd>=0&&close(fd)==0;}
static int indexes(unsigned *main_index,unsigned *bridge_index)
{
 struct stat st;
 *main_index=if_nametoindex("ra0");*bridge_index=if_nametoindex("br0");
 return *main_index&&*bridge_index&&*main_index!=*bridge_index&&
  !stat("/sys/class/net/br0/bridge",&st)&&S_ISDIR(st.st_mode);
}
int wr_iot_restart_main_bridge_current(void)
{
 unsigned m,b,after_m,after_b;
 return guard()&&indexes(&m,&b)&&master()==1&&indexes(&after_m,&after_b)&&
  m==after_m&&b==after_b&&guard();
}
enum wr_iot_main_bridge_result wr_iot_restart_main_bridge_attach(void)
{
 struct ifreq r={0};unsigned m,b,after_m,after_b;int fd,result,closed,state;
 if(!guard()||!indexes(&m,&b))return WR_MAIN_BRIDGE_REFUSED;
 state=master();if(state<0)return WR_MAIN_BRIDGE_REFUSED;
 if(state==1)return wr_iot_restart_main_bridge_current()?WR_MAIN_BRIDGE_ATTACHED:WR_MAIN_BRIDGE_REFUSED;
 fd=socket(AF_INET,SOCK_DGRAM|SOCK_CLOEXEC,0);if(fd<0)return WR_MAIN_BRIDGE_REFUSED;
 memcpy(r.ifr_name,"ra0",4);
 if(ioctl(fd,SIOCGIFFLAGS,&r)||!(r.ifr_flags&IFF_UP)||master()!=0||
    !indexes(&after_m,&after_b)||after_m!=m||after_b!=b||!guard()){
  (void)close(fd);return WR_MAIN_BRIDGE_REFUSED;
 }
 memset(&r,0,sizeof(r));memcpy(r.ifr_name,"br0",4);r.ifr_ifindex=(int)m;
 result=ioctl(fd,SIOCBRADDIF,&r);closed=close(fd);
 if(result||closed)return WR_MAIN_BRIDGE_UNCERTAIN;
 return wr_iot_restart_main_bridge_current()?WR_MAIN_BRIDGE_ATTACHED:WR_MAIN_BRIDGE_UNCERTAIN;
}
