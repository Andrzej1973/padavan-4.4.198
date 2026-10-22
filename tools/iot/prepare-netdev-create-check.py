#!/usr/bin/env python3
"""Isolated mt76x3 netdev name-failure repair, not a production installer."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('input', type=Path)
p.add_argument('candidate', type=Path)
p.add_argument('fixture', type=Path)
a = p.parse_args()
if len({x.resolve() for x in (a.input, a.candidate, a.fixture)}) != 3:
    raise SystemExit('Input and outputs must be distinct')
if a.candidate.exists() or a.fixture.exists():
    raise SystemExit('Refusing to overwrite outputs')
source = a.input.read_text(encoding='utf-8')
anchor = 'PNET_DEV RtmpOSNetDevCreate('
if source.count(anchor) != 1:
    raise SystemExit('Netdevice create signature changed')
start = source.index(anchor)
end = source.index('\n}', start) + 2
original = source[start:end]
name_call = 'status = RtmpOSNetDevRequestName('
if original.count(name_call) != 1:
    raise SystemExit('Name allocation call changed')
offset = original.index(name_call)
before, after = original[:offset], original[offset:]
old = '\t\tRtmpOSNetDevFree(pNetDev);'
if after.count(old) != 1:
    raise SystemExit('Name allocation failure cleanup changed')
patched = before + after.replace(old, '''#if LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,31)
        /* This private ops allocation has not been handed to Detach. */
        vfree(pNetDevOps);
        pNetDev->netdev_ops = NULL;
#endif
        RtmpOSNetDevFree(pNetDev);''')
prefix = r'''#include <assert.h>
#include <string.h>
#include <stdio.h>
typedef int INT32;
typedef int INT;
/* Vendor IN is a direction annotation; mark intentionally unused arguments. */
#define IN __attribute__((unused))
typedef unsigned int UINT32;
typedef char RTMP_STRING;
typedef void *PVOID;
struct net_device_ops {int marker;};
struct net_device {const struct net_device_ops *netdev_ops;};
typedef struct net_device *PNET_DEV;
static struct net_device device;
static struct net_device_ops ops;
static int fail_device,fail_ops,fail_name,device_owned,ops_owned,device_frees,ops_frees,name_calls;
#define KERNEL_VERSION(a,b,c) (((a)<<16)|((b)<<8)|(c))
#ifndef LINUX_VERSION_CODE
#define LINUX_VERSION_CODE KERNEL_VERSION(4,4,198)
#endif
#define NDIS_STATUS_SUCCESS 0
#define RT_DEBUG_ERROR 0
#define RT_DEBUG_TRACE 1
#define DBGPRINT(level,args) ((void)0)
static int RtmpOSNetDevAlloc(PNET_DEV *out,int size){
 assert(size==16&&!device_owned);if(fail_device)return 1;
 device_owned=1;*out=&device;return 0;
}
#if LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,31)
static int RtmpOSNetDevOpsAlloc(PVOID *out){
 assert(device_owned&&!ops_owned);if(fail_ops)return 1;
 ops_owned=1;*out=&ops;return 0;
}
static void vfree(const void *p){assert(p==&ops&&ops_owned);ops_owned=0;ops_frees++;}
#endif
static void RtmpOSNetDevFree(PNET_DEV d){
 assert(d==&device&&device_owned&&!ops_owned&&!d->netdev_ops);
 device_owned=0;device_frees++;
}
static int RtmpOSNetDevRequestName(INT32 row,UINT32 *io,PNET_DEV d,char *name,int index){
 assert(row==0&&*io==0&&d==&device&&!strcmp(name,"ra")&&index==2);
 name_calls++;return fail_name;
}
'''
tail = r'''
static void reset(void){
 assert(!device_owned&&!ops_owned);memset(&device,0,sizeof(device));
 fail_device=fail_ops=fail_name=device_frees=ops_frees=name_calls=0;
}
static PNET_DEV create(void){UINT32 io=0;return RtmpOSNetDevCreate(0,&io,2,2,16,"ra");}
int main(void){
 reset();fail_device=1;assert(!create()&&!device_owned&&!ops_owned&&!device_frees&&!ops_frees&&!name_calls);
#if LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,31)
 reset();fail_ops=1;assert(!create()&&!device_owned&&!ops_owned&&device_frees==1&&!ops_frees&&!name_calls);
#endif
 reset();fail_name=1;assert(!create()&&!device_owned&&!ops_owned&&device_frees==1&&name_calls==1);
#if LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,31)
 assert(ops_frees==1);
#else
 assert(!ops_frees);
#endif
 reset();assert(create()==&device&&device_owned&&!device_frees&&!ops_frees&&name_calls==1);
#if LINUX_VERSION_CODE >= KERNEL_VERSION(2,6,31)
 assert(ops_owned&&device.netdev_ops==&ops);vfree(device.netdev_ops);device.netdev_ops=NULL;
#endif
 RtmpOSNetDevFree(&device);
 puts("PASS candidate actual RtmpOSNetDevCreate: allocation/name failures release owned memory, success retains ownership; operations injected");
 return 0;
}
'''
a.candidate.write_text(source[:start] + patched + source[end:], encoding='utf-8')
a.fixture.write_text(prefix + patched + tail, encoding='utf-8')
print('Prepared isolated create candidate; production unchanged')
