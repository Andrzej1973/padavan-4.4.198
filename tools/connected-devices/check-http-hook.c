#define _GNU_SOURCE
#define BOARD_WR1200JS 1
#define WR_DEVICE_SOURCE_PATH "source"
#define WR_DEVICE_LOCK_PATH "networkmap.lock"
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <assert.h>
#include <string.h>
static unsigned int current_uptime;
static unsigned int uptime(void){return current_uptime;}
#include "http-hook.inc"
static int radio_failure;
int wr_device_collect_radio(struct wr_device_snapshot *snapshot){
 if(radio_failure)return 0;
 if(snapshot->count){snapshot->records[0].radio.band_mask=1;snapshot->records[0].radio.rssi[0]=-60;}
 return 1;
}
static void response(char *out,size_t capacity){FILE *fp=tmpfile();size_t n;assert(fp);do_wr_devices_json("wr_devices.json",fp);rewind(fp);n=fread(out,1,capacity-1,fp);out[n]=0;assert(!ferror(fp));assert(!fclose(fp));}
static void history_response(char *out,size_t capacity){FILE *fp=tmpfile();size_t n;assert(fp);do_wr_roaming_json("wr_roaming.json",fp);rewind(fp);n=fread(out,1,capacity-1,fp);out[n]=0;assert(!ferror(fp));assert(!fclose(fp));}
int main(int argc,char **argv){char directory[]="/tmp/device-http-XXXXXX",out[4096];FILE *fp;(void)argv;
 assert(mkdtemp(directory));assert(!chdir(directory));
 wr_device_background_tick();assert(wr_device_http_history.gap);
 response(out,sizeof(out));assert(strstr(out,"source_unavailable"));
 current_uptime=5;fp=fopen("source","w");assert(fp);assert(fputs("192.168.1.2,00:11:22:33:44:55,<script>,1,0,0\n",fp)>=0);assert(!fclose(fp));
 wr_device_background_tick();assert(wr_device_http_history.event_count==2 && !wr_device_http_history.gap);
 response(out,sizeof(out));assert(strstr(out,"\"cacheState\":\"current\"")&&wr_device_http_cache.sequence==1);
 assert(!strchr(out,'<')&&strstr(out,"\"sourceUpdatedAt\":"));
 if(argc==2)puts(out);
 response(out,sizeof(out));assert(wr_device_http_cache.collections==2);
 history_response(out,sizeof(out));assert(wr_device_http_cache.collections==2);
 assert(strstr(out,"\"kind\":\"observed\"")&&strstr(out,"\"cause\":\"unknown\"")&&strstr(out,"\"cacheState\":\"current\""));
 radio_failure=1;current_uptime=10;response(out,sizeof(out));
 assert(strstr(out,"\"cacheState\":\"stale\"") && strstr(out,"\"rssi\":-60") && wr_device_http_cache.sequence==1);
 history_response(out,sizeof(out));assert(strstr(out,"\"gap\":true")&&strstr(out,"\"cacheState\":\"stale\""));
 radio_failure=0;
 assert(!unlink("source"));current_uptime=15;response(out,sizeof(out));assert(strstr(out,"\"cacheState\":\"stale\"")&&wr_device_http_cache.sequence==1);
 assert(strstr(out,"\"collectionAgeMs\":10000"));assert(!unlink("networkmap.lock"));assert(!chdir("/tmp"));assert(!rmdir(directory));
 if(argc!=2){puts("PASS read-only HTTP hook: valid current/stale JSON, shared cache, failed-source retention and escaped names; live authentication unverified");}
 return 0;
}
