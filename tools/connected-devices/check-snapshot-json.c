#define _GNU_SOURCE
#include "snapshot-json.h"
#include <assert.h>
static struct wr_device_snapshot snapshot;
static char buffer[131072];
int main(int argc,char **argv){size_t length=99;unsigned int i;
 (void)argv;
 snapshot.count=1;strcpy(snapshot.records[0].ip,"192.168.1.2");strcpy(snapshot.records[0].mac,"00:11:22:33:44:55");
 strcpy(snapshot.records[0].name,"<script>\"\\\n\t\xc0\xaf\xcf\x80\xf0\x9f\x98\x80 Пристрій");
 assert(wr_device_snapshot_json(&snapshot,"fixture",2,buffer,sizeof(buffer),&length));assert(length==strlen(buffer));
 assert(!strchr(buffer,'<')&&!strchr(buffer,'>'));assert(strstr(buffer,"\\u003cscript\\u003e"));
 if(argc==2){puts(buffer);return 0;}
 snapshot.records[0].radio.band_mask=3;
 snapshot.records[0].radio.rssi[0]=-60; snapshot.records[0].radio.rssi[1]=-127;
 assert(wr_device_snapshot_json(&snapshot,"fixture",2,buffer,sizeof(buffer),&length));
 assert(strstr(buffer,"\"presence\":\"associated\"") && strstr(buffer,"\"rssi\":-60") && strstr(buffer,"\"rssi\":null"));
 snapshot.records[0].radio.band_mask=4;
 assert(!wr_device_snapshot_json(&snapshot,"fixture",2,buffer,sizeof(buffer),&length));
 snapshot.records[0].radio.band_mask=0;

 assert(!wr_device_snapshot_json(&snapshot,"fixture",2,buffer,10,&length)&&length==0);
 assert(!wr_device_snapshot_json(&snapshot,"fixture",9007199254740992ULL,buffer,sizeof(buffer),&length));
 snapshot.count=128;for(i=0;i<128;i++){memset(snapshot.records[i].name,1,128);snapshot.records[i].name[128]=0;}
 assert(wr_device_snapshot_json(&snapshot,"fixture",3,buffer,sizeof(buffer),&length)&&length<sizeof(buffer));
 puts("PASS bounded snapshot JSON, Unicode escaping, hostile names, output capacity and browser-safe sequence limit");return 0;
}
