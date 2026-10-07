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
int main(void)
{
    struct wr_band_settings_snapshot s={0};
    assert(!wr_band_snapshot_capture(&s,64,reader) && calls==1);
    assert(!strcmp(wr_band_snapshot_get(&s,"rt_ssid"),"same"));
    assert(!strcmp(wr_band_snapshot_get(&s,"wl_ssid"),"same"));
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
    puts("PASS immutable settings lookup, reader errors, malformed dumps, duplicates and release; actual NVRAM reader integration pending");
    return 0;
}
