#!/usr/bin/env python3
"""Actual cold parser/profile scanner/readback, with borrowed NVRAM and guard."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
body=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#include "precreated-profile.h"
#include "restart-profile.h"
static char profile_path[1024],saved_ssid[33]="IoT",saved_password[65]="iot-password",saved_enabled[2]="0",borrowed[128];
static int guard=1,reads,drift,guard_after;
#define WR_IOT_RADIO_PROFILE_PATH profile_path
const char *nvram_safe_get(const char *key){
 reads++;
 if(drift&&reads==4)strcpy(saved_ssid,"foreign");
 const char *v=!strcmp(key,"wr_iot_enable")?saved_enabled:!strcmp(key,"wr_iot_ssid")?saved_ssid:saved_password;
 snprintf(borrowed,sizeof(borrowed),"%s",v);return borrowed;
}
int wr_iot_service_guard_dup(void){if(guard_after&&reads>=6)return -1;return guard?open("/dev/null",O_RDONLY):-1;}
#include "saved-file.h"
static unsigned captures;static int mutate_second;
static int capture_hook(struct wr_iot_saved_file*out,const char*path){
 if(++captures==2&&mutate_second){
  FILE*f=fopen(path,"r+");char bytes[4096];assert(f);size_t n=fread(bytes,1,sizeof(bytes)-1,f);bytes[n]=0;
  char*c=strstr(bytes,"Channel=6\n");assert(c&&fseek(f,(long)(c-bytes)+8,SEEK_SET)==0&&fputc('7',f)!=EOF&&!fclose(f));
 }
 return wr_iot_saved_capture(out,path);
}
#define wr_iot_saved_capture capture_hook
#include "restart-profile.c"
#undef wr_iot_saved_capture
static const char baseline[]="Default\nBssidNum=2\nSSID1=Main\nSSID2=Guest\nSSID3=\nWPAPSK1=main-password\nWPAPSK2=guest-password\nWPAPSK3=\nAuthMode=WPA2PSK;OPEN\nEncrypType=AES;NONE\nWmmCapable=1;1\nDLSCapable=0;0\nNoForwarding=0;1\nHideSSID=0;0\nStationKeepAlive=0;0\nPreAuth=0;0\nIEEE8021X=0;0\nFixedTxMode=0;0\nHT_MCS=33;33\nChannel=6\nAutoChannelSelect=0\n";
static void make_profile(void){
 FILE *in=tmpfile(),*out=fopen(profile_path,"w");assert(in&&out);assert(fputs(baseline,in)>=0);rewind(in);
 assert(wr_iot_precreated_profile(in,out,"IoT","iot-password",0));assert(!fclose(in)&&!fclose(out));
}
static void replace_file(const void *data,size_t length){FILE*f=fopen(profile_path,"w");assert(f&&fwrite(data,1,length,f)==length&&!fclose(f));}
static int check(const struct wr_iot_request*r){reads=0;captures=0;return wr_iot_restart_profile_current(r);}
int main(int argc,char**argv){
 assert(argc==2&&strlen(argv[1])+16<sizeof(profile_path));snprintf(profile_path,sizeof(profile_path),"%s/profile",argv[1]);
 struct wr_iot_request desired={.enabled=1,.ssid="IoT",.password="iot-password"};
 make_profile();struct stat before,after;assert(!stat(profile_path,&before));
 assert(check(&desired));assert(!stat(profile_path,&after)&&before.st_ino==after.st_ino&&before.st_size==after.st_size);
 strcpy(saved_enabled,"1");assert(check(&desired));strcpy(saved_enabled,"0");
 mutate_second=1;assert(!check(&desired)&&captures==2);mutate_second=0;make_profile();
 guard=0;assert(!check(&desired)&&!reads);guard=1;
 strcpy(saved_password,"foreign-password");assert(!check(&desired));strcpy(saved_password,"iot-password");
 drift=1;assert(!check(&desired));drift=0;strcpy(saved_ssid,"IoT");
 guard_after=1;assert(!check(&desired));guard_after=0;
 FILE*f=fopen(profile_path,"r");char valid[4096];assert(f);size_t n=fread(valid,1,sizeof(valid),f);assert(!fclose(f)&&n<sizeof(valid));
 replace_file(valid,n);f=fopen(profile_path,"a");assert(f&&fputs("SSID3=IoT\n",f)>=0&&!fclose(f));assert(!check(&desired));
 replace_file(valid,n);char*key=strstr(valid,"WPAPSK3=iot-password");assert(key);key[8]='X';replace_file(valid,n);assert(!check(&desired));key[8]='i';
 replace_file(valid,n);valid[n/2]=0;replace_file(valid,n);assert(!check(&desired));
 assert(!unlink(profile_path));assert(!check(&desired));assert(!symlink("missing",profile_path));assert(!check(&desired));assert(!unlink(profile_path));
 assert(!mkfifo(profile_path,0600));assert(!check(&desired));assert(!unlink(profile_path));
 make_profile();f=fopen(profile_path,"a");assert(f);for(unsigned i=0;i<256U*1024U;i++)assert(fputc('x',f)!=EOF);assert(!fclose(f));assert(!check(&desired));
 assert(!unlink(profile_path));make_profile();desired.enabled=0;assert(!check(&desired));desired.enabled=1;memset(desired.ssid,'x',sizeof(desired.ssid));assert(!check(&desired));
 assert(!unlink(profile_path));
 puts("PASS read-only restart profile: saved OFF/ON credentials retained, borrowed NVRAM copied, strict third-BSS scanner, same-size mutation between double readback refused, inode unchanged, foreign credentials/drift/duplicate/NUL/symlink/FIFO/missing/oversize/guard refusal; no writes or loaded-key/radio claim");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-restart-profile-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 unit=root/'check.c';unit.write_text(body);binary=root/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),'-o',str(binary)],check=True)
 subprocess.run([str(binary),d],check=True,timeout=15)
