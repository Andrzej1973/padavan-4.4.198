#include <stdio.h>
#include <unistd.h>
static int fail_sync,fail_rename,fail_close;
static int test_sync(int fd){return fail_sync?-1:fsync(fd);}
static int test_rename(const char *a,const char *b){return fail_rename?-1:rename(a,b);}
static int test_close(FILE *f){int result=fclose(f);return fail_close?-1:result;}
#define WR_IOT_FSYNC test_sync
#define WR_IOT_RENAME test_rename
#define WR_IOT_CLOSE test_close
#include "profile-file.h"
#include <assert.h>
#include <dirent.h>
static const char profile[]="Default\nBssidNum=2\nSSID1=Main\nSSID2=Guest\nSSID3=\nWPAPSK1=main-password\nWPAPSK2=guest-password\nWPAPSK3=\nAuthMode=WPA2PSK;OPEN\nEncrypType=AES;NONE\nWmmCapable=1;1\nDLSCapable=0;0\nNoForwarding=0;1\nHideSSID=0;0\nStationKeepAlive=0;0\nPreAuth=0;0\nIEEE8021X=0;0\nFixedTxMode=0;0\nHT_MCS=33;33\n";
static void write_profile(const char *path){FILE *f=fopen(path,"w");assert(f);assert(fputs(profile,f)>=0);assert(fclose(f)==0);}
static void unchanged(const char *path){char value[4096];FILE *f=fopen(path,"r");size_t n;assert(f);n=fread(value,1,sizeof(value)-1,f);value[n]=0;assert(!strcmp(value,profile));fclose(f);}
int main(void){char dir[]="/tmp/wr-iot-profile-XXXXXX",path[256],linkpath[256],value[4096];FILE *f;size_t n;DIR *d;struct dirent *entry;struct stat st;int entries=0;
 assert(mkdtemp(dir));snprintf(path,sizeof(path),"%s/radio.dat",dir);write_profile(path);
 assert(wr_iot_profile_replace(path,NULL,NULL,0));unchanged(path);
 assert(!wr_iot_profile_replace(path,"IoT","short",1));unchanged(path);
 fail_sync=1;assert(!wr_iot_profile_replace(path,"IoT","password",1));unchanged(path);fail_sync=0;
 fail_close=1;assert(!wr_iot_profile_replace(path,"IoT","password",1));unchanged(path);fail_close=0;
 fail_rename=1;assert(!wr_iot_profile_replace(path,"IoT","password",1));unchanged(path);fail_rename=0;
 snprintf(linkpath,sizeof(linkpath),"%s/link.dat",dir);assert(!symlink(path,linkpath));assert(!wr_iot_profile_replace(linkpath,"IoT","password",1));unchanged(path);unlink(linkpath);
 assert(wr_iot_profile_replace(path,"IoT","password",1));f=fopen(path,"r");assert(f);n=fread(value,1,sizeof(value)-1,f);value[n]=0;fclose(f);assert(strstr(value,"BssidNum=3\n"));assert(strstr(value,"SSID3=IoT\n"));assert(!stat(path,&st));assert((st.st_mode&0777)==0600);
 d=opendir(dir);assert(d);while((entry=readdir(d)))if(strcmp(entry->d_name,".")&&strcmp(entry->d_name,".."))entries++;closedir(d);assert(entries==1);
 unlink(path);rmdir(dir);puts("PASS IoT atomic file candidate: old profile preserved on validation/fsync/close/rename failure, no symlink follow, private committed file, no temporary remnants");return 0;}
