#include "settings-snapshot.h"
#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
static int mode, calls;
static int reader(char *data,int capacity,int temporary)
{
    const char values[]="rt_ssid=same\0wl_ssid=same\0empty=\0";
    const char duplicate[]="a=1\0a=2\0";
    assert(capacity==64 && temporary==1);++calls;
    if (mode==1) { errno=ENOSPC;return -1; }
    if (mode==2) { memset(data,'x',(size_t)capacity);return 0; }
    if (mode==3) { memcpy(data,duplicate,sizeof(duplicate));return 0; }
    if (mode==4) { memcpy(data,"broken",6);return 0; }
    if (mode==5) return 0;
    memcpy(data,values,sizeof(values));return 0;
}
static int long_reader(char *data,int capacity,int temporary)
{
    assert(capacity==128 && temporary==1);
    memcpy(data,"rt_",3);memset(data+3,'z',60);data[63]='=';data[64]='v';
    return 0;
}
int main(void)
{
    struct wr_band_settings_snapshot s={0};
    assert(!wr_band_snapshot_capture(&s,64,reader) && calls==1);
    assert(!strcmp(wr_band_snapshot_get(&s,"rt_ssid"),"same"));
    assert(!strcmp(wr_band_snapshot_get(&s,"wl_ssid"),"same"));
    assert(!strcmp(wr_band_snapshot_wlan_get(&s,0,"ssid"),"same"));
    assert(!strcmp(wr_band_snapshot_wlan_get(&s,1,"ssid"),"same"));
    assert(!wr_band_snapshot_wlan_get(&s,2,"ssid"));
    assert(!wr_band_snapshot_wlan_get(&s,0,"ssid=other"));
    assert(!wr_band_snapshot_wlan_get(&s,0,""));
    {
        char long_name[80];memset(long_name,'x',sizeof(long_name));
        assert(!wr_band_snapshot_wlan_get(&s,0,long_name));
    }
    assert(!strcmp(wr_band_snapshot_get(&s,"empty"),""));
    assert(!wr_band_snapshot_get(&s,"rt") && !wr_band_snapshot_get(&s,"missing"));
    mode=1;
    assert(!strcmp(wr_band_snapshot_get(&s,"rt_ssid"),"same") && calls==1);
    assert(wr_band_snapshot_capture(&s,64,reader)==-1 && calls==1);
    wr_band_snapshot_release(&s);assert(!s.data && !s.capacity);
    for(mode=1;mode<=4;++mode) {
        assert(wr_band_snapshot_capture(&s,64,reader)==-1 && !s.data && !s.capacity);
        assert(errno==(mode==1?ENOSPC:EPROTO));
    }
    mode=5;
    assert(!wr_band_snapshot_capture(&s,64,reader) && !wr_band_snapshot_get(&s,"rt_ssid"));
    wr_band_snapshot_release(&s);wr_band_snapshot_release(&s);
    assert(wr_band_snapshot_capture(&s,1,reader)==-1 && !s.data);
    {
        char name[62];memset(name,'z',61);name[60]=0;
        assert(!wr_band_snapshot_capture(&s,128,long_reader));
        assert(!strcmp(wr_band_snapshot_wlan_get(&s,0,name),"v"));
        name[60]='z';name[61]=0;
        assert(!wr_band_snapshot_wlan_get(&s,0,name));
        wr_band_snapshot_release(&s);
    }
    puts("PASS immutable settings lookup, reader errors, malformed dumps, duplicates and release; actual NVRAM reader integration pending");
    return 0;
}
