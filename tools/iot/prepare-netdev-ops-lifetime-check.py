#!/usr/bin/env python3
"""Execute real Detach/Protect/Free functions with modeled kernel retirement."""
import argparse,re
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new fixture output required')
s=(a.candidate/'os/linux/rt_linux.c').read_text()
def function(sig):
 start=s.index(sig);return s[start:s.index('\n}',start)+2]
detach=function('void RtmpOSNetDevDetach(');protect=function('void RtmpOSNetDevProtect(');free=function('void RtmpOSNetDevFree(')
assert 'vfree(' not in detach and 'vfree((void *)pNetDev->netdev_ops);' in free
assert free.index('vfree(')<free.index('pNetDev->netdev_ops = NULL;')<free.index('free_netdev(')
for rel in ['ap/ap_mbss.c','ap/ap_apcli.c','ap/ap_wds.c','sniffer/sniffer_radiotap.c','os/linux/pci_main_dev.c']:
 text=(a.candidate/rel).read_text()
 assert not re.search(r'vfree\([^;]*netdev_ops',text),rel
create=function('PNET_DEV RtmpOSNetDevCreate(')
assert 'vfree(' not in create and 'pNetDev->netdev_ops = NULL;' not in create
prefix=r'''
#include <assert.h>
#include <stddef.h>
#define KERNEL_VERSION(a,b,c) (((a)<<16)|((b)<<8)|(c))
#define LINUX_VERSION_CODE KERNEL_VERSION(4,4,198)
#define ASSERT assert
typedef int BOOLEAN;
struct net_device {const void *netdev_ops;int registered,drained,freed;};
typedef struct net_device *PNET_DEV;
static PNET_DEV pending;static int held,ops_frees,device_frees;
static void rtnl_lock(void){assert(!held);held=1;}
static void unregister_netdevice(PNET_DEV d){assert(held&&d->registered);pending=d;d->registered=0;assert(d->netdev_ops);}
static void rtnl_unlock(void){assert(held);held=0;if(pending){assert(pending->netdev_ops);pending->drained=1;pending=NULL;}}
static void vfree(void *p){if(p){assert(!held);ops_frees++;}}
static void free_netdev(PNET_DEV d){assert(!held&&!d->registered&&!d->netdev_ops&&!d->freed);d->freed=1;device_frees++;}
'''
create_shim=r'''
typedef int INT;typedef int INT32;typedef unsigned int UINT32;typedef void *PVOID;typedef char RTMP_STRING;
#define IN __attribute__((unused))
#define NDIS_STATUS_SUCCESS 0
#define DBGPRINT(l,a) ((void)0)
struct net_device_ops {int marker;};
static struct net_device created;static struct net_device_ops created_ops;
static int fail_device,fail_ops,fail_name;
static int RtmpOSNetDevAlloc(PNET_DEV *out,int size){(void)size;if(fail_device)return 1;created=(struct net_device){0};*out=&created;return 0;}
static int RtmpOSNetDevOpsAlloc(PVOID *out){if(fail_ops)return 1;*out=&created_ops;return 0;}
static int RtmpOSNetDevRequestName(INT32 row,UINT32 *io,PNET_DEV d,RTMP_STRING *name,int index){
(void)row;(void)io;(void)d;(void)name;(void)index;return fail_name;}
'''
post=r'''
int main(void){int ops;struct net_device registered={&ops,1,0,0},failed={&ops,0,0,0},no_ops={0};
RtmpOSNetDevProtect(1);RtmpOSNetDevDetach(&registered);
assert(!ops_frees&&!device_frees&&registered.netdev_ops&&!registered.drained);
RtmpOSNetDevProtect(0);assert(registered.drained&&registered.netdev_ops&&!ops_frees);
RtmpOSNetDevFree(&registered);assert(ops_frees==1&&device_frees==1);
RtmpOSNetDevFree(&failed);assert(ops_frees==2&&device_frees==2);
RtmpOSNetDevFree(&no_ops);assert(ops_frees==2&&device_frees==3);
ops_frees=device_frees=0;
{UINT32 io=0;fail_device=1;assert(!RtmpOSNetDevCreate(0,&io,0,0,0,"ra"));assert(!ops_frees&&!device_frees);
fail_device=0;fail_ops=1;assert(!RtmpOSNetDevCreate(0,&io,0,0,0,"ra"));assert(!ops_frees&&device_frees==1);
fail_ops=0;fail_name=1;assert(!RtmpOSNetDevCreate(0,&io,0,0,0,"ra"));assert(ops_frees==1&&device_frees==2);
fail_name=0;assert(RtmpOSNetDevCreate(0,&io,0,0,0,"ra")==&created);assert(created.netdev_ops==&created_ops);
RtmpOSNetDevFree(&created);assert(ops_frees==2&&device_frees==3);}
return 0;}
'''
a.output.write_text(prefix+detach+protect+free+create_shim+create+post,encoding='utf-8')
print('Extracted Detach/Protect/Free; RTNL/ref drain and allocation operations modeled')
