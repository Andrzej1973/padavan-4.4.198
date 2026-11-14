#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <net/if.h>
#include "restart-multicast.h"
#include "service-guard.h"
#ifndef WR_IOT_MULTICAST_SYSFS
#define WR_IOT_MULTICAST_SYSFS "/sys/class/net"
#endif
static int mc_guard(void)
{int fd=wr_iot_service_guard_dup();return fd>=0&&close(fd)==0;}
static int mc_context(unsigned bss,unsigned *index)
{
 char path[256],target[256];ssize_t n;const char*name=bss==0?"ra0":"ra1";
 if(bss>1||!mc_guard())return 0;
 *index=if_nametoindex(name);if(!*index)return 0;
 if(snprintf(path,sizeof(path),"%s/%s/master",WR_IOT_MULTICAST_SYSFS,name)>=(int)sizeof(path))return 0;
 n=readlink(path,target,sizeof(target)-1);if(n<=0||(size_t)n>=sizeof(target)-1)return 0;
 target[n]=0;{char*last=strrchr(target,'/');return last&&!strcmp(last+1,"br0");}
}
static int mc_file(unsigned bss,unsigned attr,int enabled,int write_value)
{
 static const char*const fields[]={"multicast_fast_leave","multicast_to_unicast"};
 char path[256];FILE*f;int ok,c,end;
 if(bss>1||attr>1||(enabled!=0&&enabled!=1))return 0;
 if(snprintf(path,sizeof(path),"%s/ra%u/brport/%s",WR_IOT_MULTICAST_SYSFS,bss,fields[attr])>=(int)sizeof(path))return 0;
 f=fopen(path,write_value?"r+":"r");if(!f)return 0;
 if(write_value)ok=fputs(enabled?"1\n":"0\n",f)>=0;
 else{c=fgetc(f);end=fgetc(f);ok=c==(enabled?'1':'0')&&end=='\n'&&fgetc(f)==EOF&&!ferror(f);}
 if(fclose(f))ok=0;
 return ok;
}
int wr_iot_restart_multicast_current(unsigned bss,int enabled)
{
 unsigned before,after;
 return mc_context(bss,&before)&&mc_file(bss,0,enabled,0)&&mc_file(bss,1,enabled,0)&&
        mc_context(bss,&after)&&before==after;
}
int wr_iot_restart_multicast_apply(unsigned bss,int enabled)
{
 unsigned before,after;unsigned attr;
 if((enabled!=0&&enabled!=1)||!mc_context(bss,&before))return 0;
 for(attr=0;attr<2;attr++){
  if(!mc_context(bss,&after)||before!=after||!mc_file(bss,attr,enabled,1)||
     !mc_file(bss,attr,enabled,0))return 0;
 }
 return mc_context(bss,&after)&&before==after&&wr_iot_restart_multicast_current(bss,enabled);
}
