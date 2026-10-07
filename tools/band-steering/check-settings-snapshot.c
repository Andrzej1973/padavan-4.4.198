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
static int wep_mode;
static int wep_reader(char *data,int capacity,int temporary)
{
    static const char *const dumps[]={
        "rt_key=2\0rt_key2=abcde\0rt_key_type=0\0wl_key=4\0wl_key4=0123456789\0wl_key_type=1\0",
        "rt_key=0\0rt_key1=abcdefghijklm\0rt_key_type=0\0wl_key=5\0wl_key1=01234567890123456789012345\0",
        "rt_key=3\0rt_key3=bad\0rt_key_type=original\0wl_key=3\0wl_key3=bad\0",
        "rt_key= +2trailing\0rt_key2=abcde\0wl_key=999999999999999999999999999999\0wl_key1=abcde\0",
        "rt_key1=abcde\0wl_key_type=retained\0"
    };
    const char *p=dumps[wep_mode];size_t offset=0;
    assert(capacity==256 && temporary==1);
    while(*p) { size_t n=strlen(p)+1;assert(offset+n<256);memcpy(data+offset,p,n);offset+=n;p+=n; }
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
    for(wep_mode=0;wep_mode<5;++wep_mode) {
        const char *type;char before[256];
        assert(!wr_band_snapshot_capture(&s,256,wep_reader));
        memcpy(before,s.data,sizeof(before));
        type=wr_band_snapshot_wlan_key_type(&s,0);
        assert(type && !strcmp(type,wep_mode==2?"original":"1"));
        type=wr_band_snapshot_wlan_key_type(&s,1);
        if(wep_mode==2) assert(!type);
        else assert(type && !strcmp(type,wep_mode<2?"0":wep_mode==4?"retained":"1"));
        assert(!wr_band_snapshot_wlan_key_type(&s,2));
        assert(!memcmp(before,s.data,sizeof(before)));
        wr_band_snapshot_release(&s);
    }
    assert(!wr_band_snapshot_wlan_key_type(&s,0));
    puts("PASS immutable settings lookup, WEP type derivation, reader errors, malformed dumps, duplicates and release; actual NVRAM reader integration pending");
    return 0;
}
