#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include "restart-guest-isolation.h"
#include "restart-guest-up.h"
#include "service-guard.h"
#ifndef WR_IOT_GUEST_ISOLATE_PATH
#define WR_IOT_GUEST_ISOLATE_PATH "/sys/class/net/ra1/brport/isolate_mode"
#endif
static int isolation_guard(void)
{int fd=wr_iot_service_guard_dup();return fd>=0&&close(fd)==0;}
static int guest_down_in_lan(void)
{
 char link[256];ssize_t n;int up;
 if(!wr_iot_restart_guest_admin_state(&up)||up)return 0;
 n=readlink("/sys/class/net/ra1/master",link,sizeof(link)-1);
 if(n<=0||(size_t)n>=sizeof(link)-1)return 0;
 link[n]=0;{char *last=strrchr(link,'/');return last&&!strcmp(last+1,"br0");}
}
int wr_iot_restart_guest_isolation_current(int enabled)
{
 FILE *f;int c,end,ok;
 if((enabled!=0&&enabled!=1)||!isolation_guard())return 0;
 f=fopen(WR_IOT_GUEST_ISOLATE_PATH,"r");if(!f)return 0;
 c=fgetc(f);end=fgetc(f);ok=c==(enabled?'1':'0')&&end=='\n'&&fgetc(f)==EOF&&!ferror(f);
 if(fclose(f))ok=0;
 return ok&&isolation_guard();
}
int wr_iot_restart_guest_isolation_prepare(int enabled)
{
 FILE *f;int ok,c,end;
 if((enabled!=0&&enabled!=1)||!isolation_guard()||!guest_down_in_lan())return 0;
 f=fopen(WR_IOT_GUEST_ISOLATE_PATH,"w");if(!f)return 0;
 ok=fputs(enabled?"1\n":"0\n",f)>=0;if(fclose(f))ok=0;
 if(!ok||!guest_down_in_lan()||!isolation_guard())return 0;
 f=fopen(WR_IOT_GUEST_ISOLATE_PATH,"r");if(!f)return 0;
 c=fgetc(f);end=fgetc(f);
 ok=c==(enabled?'1':'0')&&end=='\n'&&fgetc(f)==EOF&&!ferror(f);
 if(fclose(f))ok=0;
 return ok&&guest_down_in_lan()&&isolation_guard();
}
