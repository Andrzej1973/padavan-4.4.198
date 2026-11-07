#!/usr/bin/env python3
"""Extract actual RC profile completion, preserving coordinated I/O behavior."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
s=(a.source/'trunk/user/rc/ralink.c').read_text(encoding='utf-8')
if 'wr_iot_precreated_boot_request_read' in s:
 reader_start=s.index('static const char *wr_iot_cold_nvram_read(')
 reader_end=s.index('\n}',reader_start)
 reader=s[reader_start:reader_end]
 snapshot='wr_profile_wlan_get_int(is_aband, "mode_x")' in s
 expected='wr_profile_safe_get' if snapshot else 'nvram_safe_get'
 assert 'return '+expected+'(key);' in reader, 'Cold credentials bypass profile snapshot'
 start=s.index('\t/* Reserve ra2 only while generating')
 end=s.index('\n#endif',start)
 block=s[start:end]
 keys=['WmmCapable','DLSCapable','NoForwarding','NoForwardingMBCast','HideSSID','StationKeepAlive','AuthMode','EncrypType','PreAuth','IEEE8021X','FixedTxMode','HT_MCS']
 statements=[]
 for key in keys:
  matches=[line.strip() for line in s.splitlines() if 'fprintf(fp, "'+key+'=' in line]
  assert len(matches)==1,(key,matches)
  if key=='EncrypType':
   statements.append('c_val_mbss[0]="AES";c_val_mbss[1]="NONE";')
  statements.extend(matches)
 for marker in ['if (iot_reserved) fprintf(fp, "SSID%d=', 'if (iot_reserved) fprintf(fp, "WPAPSK%d=']:
  matches=[line.strip() for line in s.splitlines() if marker in line]
  assert len(matches)==1,marker
  statements.extend(matches)
 writer='''
static void check_fields(void){
 for(int iot_reserved=0;iot_reserved<=1;iot_reserved++){
  FILE *fp=tmpfile();char result[2048];size_t n;
  int i_wmm=1,i_val=0,i_val_mbss[2]={0,1},i_fphy[2]={0,2};
  const char *c_val_mbss[2]={"WPA2PSK","OPEN"};assert(fp);
  struct wr_iot_precreated_profile_request iot_request={0};
  strcpy(iot_request.ssid,"Reserved-IoT");strcpy(iot_request.password,"separate-password");
'''+ '\n'.join(statements)+r'''
  rewind(fp);n=fread(result,1,sizeof(result)-1,fp);result[n]=0;fclose(fp);
  assert(strstr(result,iot_reserved?"AuthMode=WPA2PSK;OPEN;WPA2PSK\n":"AuthMode=WPA2PSK;OPEN\n"));
  assert(strstr(result,iot_reserved?"EncrypType=AES;NONE;AES\n":"EncrypType=AES;NONE\n"));
  assert((strstr(result,"SSID3=Reserved-IoT\n")!=NULL)==iot_reserved);
  assert((strstr(result,"WPAPSK3=separate-password\n")!=NULL)==iot_reserved);
  assert(strstr(result,iot_reserved?"HideSSID=0;1;0\n":"HideSSID=0;1\n"));
  assert(strstr(result,iot_reserved?"IEEE8021X=0;0;0\n":"IEEE8021X=0;0\n"));
  assert(strstr(result,iot_reserved?"FixedTxMode=0;2;0\n":"FixedTxMode=0;2\n"));
  assert(strstr(result,iot_reserved?"HT_MCS=0;1;33\n":"HT_MCS=0;1\n"));
 }
}
'''
 assert r'\t' not in block, 'Generator emitted literal backslash-t into C'
 assert 'wr_iot_profile_t") == 1' not in s
 header=(Path(__file__).resolve().parent/'precreated-profile-request.h').as_posix()
 prefix='''#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "'''+header+'''"
static const char *saved_enable="0",*saved_ssid="IoT",*saved_key="password";
static int entropy_ready=1,entropy_calls;
static const char *wr_iot_cold_nvram_read(void *unused,const char *key){
 (void)unused;
 if(!strcmp(key,"wr_iot_enable"))return saved_enable;
 if(!strcmp(key,"wr_iot_ssid"))return saved_ssid;
 assert(!strcmp(key,"wr_iot_psk"));return saved_key;
}
static int wr_iot_precreated_entropy(void *unused,unsigned char *p,unsigned int n){
 (void)unused;entropy_calls++;if(!entropy_ready)return -1;
 memset(p,0x5a,n);return (int)n;
}
static int reserve(int is_aband,int is_soc_ap,int i_mode_x){
 int i_ssid_num=2,iot_reserved=0;
 struct wr_iot_precreated_profile_request iot_request;
'''
 tail='''
 assert(iot_reserved==(i_ssid_num==3));
 return i_ssid_num;
}
int main(void){
 check_fields();
 assert(reserve(0,1,0)==3);
 saved_enable="1";assert(reserve(0,1,0)==3);
 assert(reserve(1,1,0)==2&&reserve(0,0,0)==2);
 assert(reserve(0,1,1)==2&&reserve(0,1,3)==2);
 saved_key="short";assert(reserve(0,1,0)==2);
 saved_enable="0";saved_ssid=saved_key="";
 entropy_ready=0;assert(reserve(0,1,0)==2);
 entropy_ready=1;assert(reserve(0,1,0)==3&&entropy_calls==2);
 saved_enable="1";assert(reserve(0,1,0)==2&&entropy_calls==2);
 puts("PASS actual cold generator admission: saved OFF/ON, unsupported band/mode, invalid config, unavailable entropy, factory OFF and empty ON refusal");
 return 0;
}
'''
 prefix=prefix.replace('static int reserve(',writer+'\nstatic int reserve(',1)
 a.output.write_text(prefix+block+tail,encoding='utf-8')
 raise SystemExit(0)
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
 if(!strcmp(key,"wr_iot_ssid_t"))value=ssid_value;
 else {assert(!strcmp(key,"wr_iot_psk_t"));value=password_value;}
 assert(strlen(value)<sizeof(scratch));strcpy(scratch,value);return scratch;
}
static int test_ferror(FILE *fp){(void)fp;return write_error;}
static int test_fclose(FILE *fp){(void)fp;closes++;return close_error;}
static int wr_iot_profile_apply(const char *path,const char *ssid,const char *password){
 struct wr_shared_wifi_fields f={ssid,"psk","0","2","aes",password};
 assert(!strcmp(path,"radio.dat"));assert(!strcmp(ssid,ssid_value));assert(!strcmp(password,password_value));applies++;
 return apply_ok&&wr_shared_wifi_validate(&f)==WR_SHARED_WIFI_OK;
}
#ifdef ferror
#undef ferror
#endif
#define ferror test_ferror
#ifdef fclose
#undef fclose
#endif
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
