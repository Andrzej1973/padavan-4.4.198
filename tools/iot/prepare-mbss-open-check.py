#!/usr/bin/env python3
"""Prepare isolated MBSS open-status/reference repair and wrapper fixture.

Does not edit the input driver or install a production patch. Beacon/hardware
recovery after failed open remains a separate requirement.
"""
import argparse
import hashlib
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('input',type=Path)
p.add_argument('candidate',type=Path)
p.add_argument('fixture',type=Path)
a=p.parse_args()
if len({x.resolve() for x in (a.input,a.candidate,a.fixture)})!=3:
    raise SystemExit('Input and outputs must be distinct')
if a.candidate.exists() or a.fixture.exists():
    raise SystemExit('Refusing to overwrite existing outputs')
data=a.input.read_bytes()
if hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()!='7c736a04eeeddace0bbb0c5c96198d0738f400a2':
    raise SystemExit('Unreviewed MBSS wrapper source')
source=data.decode('utf-8')
anchor='INT MBSS_VirtualIF_Open(PNET_DEV pDev)'
if source.count(anchor)!=1:
    raise SystemExit('MBSS open function changed')
start=source.index(anchor)
end=source.index('\n}',start)+2
original=source[start:end]
old='\tRTMP_AP_IoctlHandle(pAd, NULL, CMD_RTPRIV_IOCTL_MBSS_OPEN, 0, pDev, 0);'
if original.count(old)!=1:
    raise SystemExit('MBSS open ioctl changed')
patched=original.replace(old,'''\tif (RTMP_AP_IoctlHandle(pAd, NULL, CMD_RTPRIV_IOCTL_MBSS_OPEN, 0, pDev, 0)
        != NDIS_STATUS_SUCCESS) {
        RT_MOD_DEC_USE_COUNT();
        return -1;
    }''',1)
old='\tif (VIRTUAL_IF_UP(pAd) != 0)\n\t\treturn -1;'
if patched.count(old)!=1:
    raise SystemExit('MBSS failure branch changed')
patched=patched.replace(old,'''\tif (VIRTUAL_IF_UP(pAd) != 0) {
        /* VIRTUAL_IF_UP already restores its virtual-interface count.
         * Balance only the module reference acquired by this wrapper.
         * This does not establish beacon/hardware recovery. */
        RT_MOD_DEC_USE_COUNT();
        return -1;
    }''')
candidate=source[:start]+patched+source[end:]
close_anchor='INT MBSS_VirtualIF_Close(PNET_DEV pDev)'
if source.count(close_anchor)!=1:
    raise SystemExit('MBSS close function changed')
close_start=source.index(close_anchor)
close_end=source.index('\n}',close_start)+2
close_function=source[close_start:close_end]
fixture=r'''#include <assert.h>
#include <stdio.h>
typedef int INT;
typedef void VOID;
typedef void *PNET_DEV;
static int refs,virtual_refs,up_result,open_result,up_calls,ioctls,queue_started,cr_enabled,hnat;
static int closes,hardware_closes,queue_stops;
static int adapter,device;
#define RT_MOD_INC_USE_COUNT() (++refs)
#define RT_MOD_DEC_USE_COUNT() (--refs)
#define RT_DEBUG_TRACE 0
#define DBGPRINT(level,args) ((void)0)
#define RTMP_OS_NETDEV_GET_DEVNAME(dev) "ra2"
#define RTMP_OS_NETDEV_GET_PRIV(dev) (&adapter)
#define CMD_RTPRIV_IOCTL_MBSS_OPEN 1
#define CMD_RTPRIV_IOCTL_MBSS_CR_ENABLE 2
#define CMD_RTPRIV_IOCTL_MBSS_CLOSE 3
#define CMD_RTPRIV_IOCTL_MBSS_CR_DISABLE 4
#define NDIS_STATUS_SUCCESS 0
static int RTMP_AP_IoctlHandle(void *ad,void *unused,int command,int z,void *dev,int n){
 assert(ad==&adapter&&!unused&&!z&&dev==&device&&!n);ioctls++;
 if(command==1)return open_result;
 if(command==2)cr_enabled++;
 if(command==3)closes++;
 if(command==4)cr_enabled--;
 return NDIS_STATUS_SUCCESS;
}
static int VIRTUAL_IF_UP(void *ad){
 assert(ad==&adapter);up_calls++;virtual_refs++;
 if(up_result)virtual_refs--;
 return up_result;
}
static void VIRTUAL_IF_DOWN(void *ad){
 assert(ad==&adapter&&virtual_refs>0);
 if(!--virtual_refs)hardware_closes++;
}
#define RT_MOD_HNAT_REG(dev) (++hnat)
#define RT_MOD_HNAT_DEREG(dev) (--hnat)
#define RTMP_OS_NETDEV_START_QUEUE(dev) (++queue_started)
#define RTMP_OS_NETDEV_STOP_QUEUE(dev) (++queue_stops)
'''+patched+'\n'+close_function+r'''
int main(void){
 open_result=-1;
 assert(MBSS_VirtualIF_Open(&device)==-1);
 assert(!refs&&!virtual_refs&&ioctls==1&&!up_calls&&!queue_started&&!cr_enabled&&!hnat);
 open_result=0;ioctls=0;
 up_result=-1;
 assert(MBSS_VirtualIF_Open(&device)==-1);
 assert(!refs&&!virtual_refs&&ioctls==1&&!queue_started&&!cr_enabled&&!hnat);
 up_result=0;ioctls=0;
 assert(!MBSS_VirtualIF_Open(&device));
 assert(refs==1&&virtual_refs==1&&ioctls>=1&&queue_started==1);
#ifdef MT_MAC
 assert(cr_enabled==1);
#ifdef CONFIG_RA_HW_NAT_WIFI_NEW_ARCH
 assert(hnat==1);
#else
 assert(!hnat);
#endif
#else
 assert(!cr_enabled&&!hnat);
#endif
 assert(!MBSS_VirtualIF_Close(&device));
 assert(!refs&&!virtual_refs&&closes==1&&hardware_closes==1&&queue_stops==1);
#ifdef MT_MAC
 assert(!cr_enabled);
#endif
#if defined(MT_MAC) && defined(CONFIG_RA_HW_NAT_WIFI_NEW_ARCH)
 assert(!hnat);
#endif
 /* A pre-existing main interface must retain its own reference/state. */
 refs=virtual_refs=1;
 assert(!MBSS_VirtualIF_Open(&device)&&refs==2&&virtual_refs==2);
 assert(!MBSS_VirtualIF_Close(&device)&&refs==1&&virtual_refs==1);
 assert(hardware_closes==1);
 puts("PASS actual candidate MBSS lifecycle: ioctl failure stops before virtual-up, failed-open reference balance, successful close, existing main reference retained; driver operations injected");
 return 0;
}
'''
if a.input.read_bytes()!=data:
    raise SystemExit('Input changed')
a.candidate.write_text(candidate,encoding='utf-8')
a.fixture.write_text(fixture,encoding='utf-8')
print('Prepared isolated MBSS open-status/reference repair; production and radio recovery unmodified')
