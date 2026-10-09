#!/usr/bin/env python3
"""Extract actual RC profile completion, preserving coordinated I/O behavior."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
s=(a.source/'trunk/user/rc/ralink.c').read_text(encoding='utf-8')
start=s.index('#if defined(BOARD_WR1200JS)\n if (!is_aband && nvram_get_int("wr_iot_profile_t") == 1)')
end=s.index('\n}\n\nint\ngen_ralink_config_2g',start)
completion=s[start:end]
assert 'return failed ? -1 : 0;' in completion
prefix=r"""#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "validate.h"
static int ready,ap_mode,write_error,close_error,apply_ok,closes,applies,reads;
static const char *ssid_value,*password_value;static char scratch[1024];
static int nvram_get_int(const char *key){assert(!strcmp(key,"wr_iot_profile_t"));return ready;}
static int get_ap_mode(void){return ap_mode;}
static const char *nvram_safe_get(const char *key){
 const char *value;reads++;
 if(!strcmp(key,"wr_iot_ssid"))value=ssid_value;
 else {assert(!strcmp(key,"wr_iot_psk"));value=password_value;}
 assert(strlen(value)<sizeof(scratch));strcpy(scratch,value);return scratch;
}
static int test_ferror(FILE *fp){(void)fp;return write_error;}
static int test_fclose(FILE *fp){(void)fp;closes++;return close_error;}
static int wr_iot_profile_apply(const char *path,const char *ssid,const char *password){
 struct wr_shared_wifi_fields f={ssid,"psk","0","2","aes",password};
 assert(!strcmp(path,"radio.dat"));assert(!strcmp(ssid,ssid_value));assert(!strcmp(password,password_value));applies++;
 return apply_ok&&wr_shared_wifi_validate(&f)==WR_SHARED_WIFI_OK;
}
#define ferror test_ferror
#define fclose test_fclose
static int complete(FILE *fp,int is_aband,int is_soc_ap,int i_mode_x,const char *dat_file){
"""
tail=r"""
}
static void reset(void){ready=ap_mode=write_error=close_error=closes=applies=reads=0;apply_ok=1;ssid_value="IoT";password_value="password";}
static int finish(int band,int soc,int mode){return complete(NULL,band,soc,mode,"radio.dat");}
int main(void){char long_ssid[34],long_password[66];
 reset();assert(finish(0,1,0)==0&&closes==1&&!applies&&!reads);
 reset();write_error=1;
#ifdef USE_WR_BAND_STEERING_PROFILE
 assert(finish(0,1,0)==-1&&closes==1&&!applies);
#else
 assert(finish(0,1,0)==0&&closes==1&&!applies);
#endif
 reset();ready=1;assert(finish(1,1,0)==0&&closes==1&&!applies&&!reads);
 reset();ready=1;assert(finish(0,1,0)==0&&closes==1&&applies==1&&reads==2);
 reset();ready=1;write_error=1;assert(finish(0,1,0)==-1&&closes==1&&!applies&&!reads);
 reset();ready=1;close_error=1;assert(finish(0,1,0)==-1&&closes==1&&!applies);
 reset();ready=1;ap_mode=1;assert(finish(0,1,0)==-1&&!applies);
 reset();ready=1;assert(finish(0,0,0)==-1&&!applies);
 reset();ready=1;assert(finish(0,1,1)==-1&&!applies);
 reset();ready=1;assert(finish(0,1,3)==-1&&!applies);
 memset(long_ssid,'s',33);long_ssid[33]=0;reset();ready=1;ssid_value=long_ssid;assert(finish(0,1,0)==-1&&!applies);
 memset(long_password,'p',65);long_password[65]=0;reset();ready=1;password_value=long_password;assert(finish(0,1,0)==-1&&!applies);
 reset();ready=1;password_value="short";assert(finish(0,1,0)==-1&&applies==1);
 reset();ready=1;apply_ok=0;assert(finish(0,1,0)==-1&&closes==1&&applies==1);
 puts("PASS actual RC profile completion: OFF and 5GHz preserved, single close on errors, mode/bounds rejection, credential snapshots, apply failure propagated");return 0;
}
"""
a.output.write_text(prefix+completion+tail,encoding='utf-8')
