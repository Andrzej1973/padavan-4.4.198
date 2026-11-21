#!/usr/bin/env python3
"""Extract actual wif_control for isolated HNAT mode regression checks."""
import argparse
import json
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('source',type=Path)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--disable-wifi-offload',action='store_true')
a=p.parse_args()
report=json.loads((a.source/'wifi-hwnat-source.json').read_text())
if report.get('wireless_offload_disabled',False)!=a.disable_wifi_offload:
 raise ValueError('Fixture expectation must match the prepared wireless offload policy')
s=(a.source/'trunk/user/rc/net_wifi.c').read_text(encoding='utf-8')
b=s.index('static int\nwif_control(')
e=s.index('\nvoid\nmlme_state_wl',b)
actual=s[b:e]
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(r'''#include <assert.h>
#include <stdarg.h>
#include <string.h>
#define USE_MT76X2_AP 1
#define LOGNAME "fixture"
static int mode, module_loaded, calls, registrations, requested;
#define logmessage(...) ((void)0)
static int is_module_loaded(const char *name) { assert(!strcmp(name,"hw_nat")); return module_loaded; }
static int nvram_get_int(const char *name) { assert(!strcmp(name,"hw_nat_mode")); return mode; }
static int doSystem(const char *format, ...) {
 va_list args; const char *iface;
 ++calls; va_start(args,format); iface=va_arg(args,const char *);
 assert(!strcmp(iface,"ra0"));
 if (!strcmp(format,"iwpriv %s set hw_nat_register=%d")) {
  requested=va_arg(args,int); ++registrations;
 } else { assert(!strcmp(format,"ifconfig %s %s 2>/dev/null")); (void)va_arg(args,const char *); }
 va_end(args); return registrations?0:7;
}
''' + actual + r'''
int main(void) {
 int up, loaded;
 for (mode=0; mode<4; ++mode) for (up=0; up<2; ++up) for (loaded=0; loaded<2; ++loaded) {
  int expected=up&&loaded;
  module_loaded=loaded; calls=registrations=0; requested=-1;
  assert(wif_control("ra0",up)==7);
  assert(calls==1+expected && registrations==expected);
  if (expected) assert(requested==(mode==1));
 }
 return 0;
}
''',encoding='utf-8')
print('Generated actual Wi-Fi HNAT helper fixture: 16 mode/up/module cases')

n=(a.source/'trunk/user/rc/net.c').read_text(encoding='utf-8')
b=n.index('#if defined (USE_HW_NAT)\n\tif (hwnat_allow)')
e=n.index('\n\thwnat_configure();\n#endif',b)
block=n[b:e]+'\n#endif\n'
network=a.output.with_name(a.output.stem+'-network.c')
network.write_text(r'''#include <assert.h>
#include <stdarg.h>
#include <stddef.h>
#include <string.h>
#define USE_HW_NAT 1
#define USE_MT76X2_AP 1
#define IFNAME_2G_MAIN "ra0"
#define IFNAME_5G_MAIN "rai0"
static int hwnat_allow, hwnat_loaded, hw_nat_mode, ipv6_nat;
static int loads, registrations, ipv6_calls, values[2];
static void module_smart_load(const char *name, const char *args) {
 assert(!strcmp(name,"hw_nat") && args==NULL); ++loads;
}
static int doSystem(const char *format, ...) {
 va_list args;
 if (!strcmp(format,"iwpriv %s set hw_nat_register=%d")) {
  const char *iface;
  va_start(args,format); iface=va_arg(args,const char *);
  assert(registrations<2);
  assert(!strcmp(iface,registrations?"rai0":"ra0"));
  values[registrations++]=va_arg(args,int); va_end(args);
 } else {
  assert(!strcmp(format,ipv6_nat==1?"echo 7 1 > /sys/kernel/debug/hnat/hnat_setting":"echo 7 0 > /sys/kernel/debug/hnat/hnat_setting"));
  ++ipv6_calls;
 }
 return 0;
}
static void apply_mode(void) {
''' + block + r'''
}
int main(void) {
 for (hwnat_allow=0; hwnat_allow<2; ++hwnat_allow)
 for (hwnat_loaded=0; hwnat_loaded<2; ++hwnat_loaded)
 for (hw_nat_mode=0; hw_nat_mode<4; ++hw_nat_mode)
 for (ipv6_nat=0; ipv6_nat<2; ++ipv6_nat) {
  loads=registrations=ipv6_calls=0;
  apply_mode();
  assert(loads==(hwnat_allow&&!hwnat_loaded));
  assert(ipv6_calls==loads);
  assert(registrations==2*hwnat_allow);
  if (hwnat_allow) assert(values[0]==(hw_nat_mode==1) && values[1]==(hw_nat_mode==1));
 }
 return 0;
}
''',encoding='utf-8')
print('Generated actual network HNAT setup fixture: 32 allow/loaded/mode/IPv6 cases')

b=n.index('static void\nhwnat_configure(void)')
e=n.index('\n#endif /* USE_HW_NAT */',b)
actual_log=n[b:e]
a.output.with_name(a.output.stem+'-log.c').write_text(r'''#include <assert.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#define LOGNAME "fixture"
static int mode, loaded;
static char message[160];
static int is_module_loaded(const char *name) { assert(!strcmp(name,"hw_nat")); return loaded; }
static int nvram_get_int(const char *name) { assert(!strcmp(name,"hw_nat_mode")); return mode; }
static void logmessage(const char *name, const char *format, ...) {
 va_list args; (void)name;
 va_start(args,format); vsnprintf(message,sizeof(message),format,args); va_end(args);
}
''' + actual_log + r'''
int main(void) {
 for (mode=0; mode<4; ++mode) for (loaded=0; loaded<2; ++loaded) {
  hwnat_configure();
  if (!loaded) assert(!strcmp(message,"Hardware NAT/Routing: Disabled"));
  else if (mode==1) assert(strstr(message,"requested offload [WAN]<->[LAN/WLAN]"));
  else assert(strstr(message,"requested offload [WAN]<->[LAN]"));
 }
 return 0;
}
''',encoding='utf-8')
print('Generated actual HNAT log fixture: 8 mode/module cases')
if a.disable_wifi_offload:
 # Exercise the same extracted source with legacy mode 1 still stored.
 for path in [a.output, network, a.output.with_name(a.output.stem+'-log.c')]:
  text=path.read_text(encoding='utf-8')
  text=text.replace('requested==(mode==1)', 'requested==0')
  text=text.replace('values[0]==(hw_nat_mode==1) && values[1]==(hw_nat_mode==1)', 'values[0]==0 && values[1]==0')
  text=text.replace('else if (mode==1) assert(strstr(message,"requested offload [WAN]<->[LAN/WLAN]"));', '')
  path.write_text(text,encoding='utf-8')
 print('Forced-off policy: all saved modes expect zero wireless registrations; wired module cases retained')
 for driver in ('mt76x2','mt76x3'):
  base=a.source/'trunk/linux-4.4.x/drivers/net/wireless/mediatek'/driver
  h=(base/'include/os/rt_linux.h').read_text(encoding='utf-8')
  start=h.index('#define RT_MOD_HNAT_DEREG(_net_dev)')
  end=h.index('\n#endif',start)
  macros=h[start:end]
  c=(base/'ap/ap_cfg.c').read_text(encoding='utf-8')
  start=c.rindex('INT set_hnat_register(')
  end=c.index('\n#endif /* (CONFIG_RA_HW_NAT_WIFI_NEW_ARCH) */',start)
  handler=c[start:end]
  fixture=r'''#include <assert.h>
#include <stdlib.h>
typedef int INT;
typedef unsigned int UINT32;
typedef char *PSTRING;
typedef char RTMP_STRING;
struct wifi_dev { void *if_dev; int wdev_idx; };
typedef struct { struct wifi_dev *wdev_list[3]; } RTMP_ADAPTER;
#define WDEV_NUM_MAX 3
#define TRUE 1
#define CONFIG_RA_HW_NAT_WIFI_NEW_ARCH 1
#define DBGPRINT(...) ((void)0)
#define MTWF_LOG(...) ((void)0)
static int registered, removed;
static void register_dev(void *dev) { assert(dev); ++registered; }
static void unregister_dev(void *dev) { assert(dev); ++removed; }
static void (*ppe_dev_register_hook)(void *) = register_dev;
static void (*ppe_dev_unregister_hook)(void *) = unregister_dev;
/* MT76x2 declares PSTRING *arg although PSTRING itself is char *.
 * Keep that actual vendor signature; model its byte-string conversion at
 * the opaque ABI boundary without dereferencing it as a pointer array. */
static long simple_strtol(const void *value, void *end, int base) {
 assert(end==NULL && base==10); return strtol((const char *)value,NULL,base);
}
''' + macros + '\n' + handler + r'''
int main(void) {
 int dev;
 struct wifi_dev first={&dev,0}, second={&dev,1};
 RTMP_ADAPTER adapter={{&first,NULL,&second}};
 char *requests[]={"0","1","2","-1"};
 unsigned int i;
 RT_MOD_HNAT_REG(&dev);
 assert(registered==0 && removed==1);
 for(i=0;i<sizeof(requests)/sizeof(requests[0]);++i) {
  removed=registered=0;
  assert(set_hnat_register(&adapter,(void *)requests[i])==TRUE);
  assert(registered==0 && removed==2);
 }
 ppe_dev_unregister_hook=NULL;
 RT_MOD_HNAT_REG(&dev);
 removed=registered=0;
 assert(set_hnat_register(&adapter,(void *)"1")==TRUE);
 assert(registered==0 && removed==0);
 return 0;
}
'''
  a.output.with_name('check-driver-'+driver+'.c').write_text(fixture,encoding='utf-8')
 print('Generated actual driver macro/ioctl fixtures for mt76x2 and mt76x3')
