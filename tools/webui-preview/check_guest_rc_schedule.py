#!/usr/bin/env python3
"""Execute actual pinned RC schedule function with deterministic host clock/NVRAM."""
import hashlib,pathlib,subprocess,sys,tarfile,tempfile
with tarfile.open(sys.argv[1]) as archive:
    source=archive.extractfile('trunk/user/rc/net_wifi.c').read()
text=source.decode()
start=text.index('int \ntimecheck_wifi(')
body_start=text.index('{',start)
depth=1;end=body_start+1
while depth:
    depth+=(text[end]=='{')-(text[end]=='}');end+=1
function=text[start:end]
prefix=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
static struct tm clock_fixture;
static char *days,*weekday,*weekend;
static char *nvram_wlan_get(int band,const char *key) {
 assert(band==0 || band==1);
 if(!strcmp(key,"guest_date_x")) return days;
 if(!strcmp(key,"guest_time_x")) return weekday;
 assert(!strcmp(key,"guest_time2_x"));return weekend;
}
static time_t fixture_time(time_t *out) { *out=0;return 0; }
static struct tm *fixture_localtime(const time_t *now) { (void)now;return &clock_fixture; }
#define time fixture_time
#define localtime fixture_localtime
'''
suffix=r'''
static int run(int band,int day,int minute) {
 clock_fixture.tm_wday=day;clock_fixture.tm_hour=minute/60;clock_fixture.tm_min=minute%60;
 return timecheck_wifi(band,"guest_date_x","guest_time_x","guest_time2_x");
}
int main(void) {
 int band,day,minute;
 days="1111111";weekday="08002200";weekend="10002300";
 for(band=0;band<2;band++) for(day=0;day<7;day++) for(minute=0;minute<1440;minute++) {
  int weekend_day=day==0 || day==6;
  int begin=weekend_day?600:480, end=weekend_day?1380:1320;
  assert(run(band,day,minute)==(minute>=begin && minute<=end));
 }
 days="0000010";weekday="22000800";weekend="10002300";
 for(day=0;day<7;day++) for(minute=0;minute<1440;minute++)
  assert(run(0,day,minute)==((day==5 && minute>=1320)||(day==6 && minute<=480)));
 days="0000000";
 for(day=0;day<7;day++) assert(run(0,day,600)==0);
 days="bad";assert(run(0,1,600)==1); /* Actual legacy fail-open, NOT new admission policy. */
 puts("PASS actual RC Guest schedule: both bands, inclusive bounds, Friday overnight, no days, legacy malformed-length fail-open; host only");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-guest-rc-schedule-') as scratch:
    p=pathlib.Path(scratch);(p/'fixture.c').write_text(prefix+function+suffix)
    subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(p/'fixture.c'),'-o',str(p/'fixture')],check=True)
    subprocess.run([str(p/'fixture')],check=True)
print('Pinned net_wifi.c SHA256',hashlib.sha256(source).hexdigest())
