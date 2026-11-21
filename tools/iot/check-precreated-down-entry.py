"""Actual DOWN entry/reply/reference binding with privilege and user-copy actors."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-precreated-down-reply.py')}
exec((here/'check-precreated-down-reply.py').read_text().split('with tempfile.TemporaryDirectory(',1)[0],ns)
s=ns['s']
a='#include "precreated-down-reply.inc"'
b=a+r'''
struct ifreq {void *ifr_data;};
static int permission=1,copyin_fail,copyout_fail,copyins,copyouts;
struct fake_net {int user_ns;};static struct fake_net network;
#define CAP_NET_ADMIN 12
static struct fake_net *dev_net(PNET_DEV dev){assert(dev);return &network;}
static int ns_capable(int ns,int capability){(void)ns;assert(capability==12);return permission;}
static int copy_from_user(void*out,const void*in,unsigned n){copyins++;if(copyin_fail)return 1;memcpy(out,in,n);return 0;}
static int copy_to_user(void*out,const void*in,unsigned n){copyouts++;if(copyout_fail)return 1;memcpy(out,in,n);return 0;}
#include "precreated-down-entry.inc"
'''
assert s.count(a)==1;s=s.replace(a,b)
a=' assert(!wr_iot_precreated_down_observed(&ad,&iot_device,i->generation)&&!held);'
b=r'''
 struct ifreq rq={wire};assert(wr_iot_down_query_encode(wire,64,nonce));
 permission=0;assert(wr_iot_precreated_down_ioctl(&ad,&iot_device,&rq)==-EPERM&&!copyins&&!copyouts);permission=1;
 copyin_fail=1;assert(wr_iot_precreated_down_ioctl(&ad,&iot_device,&rq)==-EFAULT&&copyins==1&&!copyouts);copyin_fail=0;
 assert(wr_iot_down_query_encode(wire,64,nonce));
 assert(!wr_iot_precreated_down_ioctl(&ad,&iot_device,&rq)&&copyins==2&&copyouts==1);
 assert(wr_iot_down_reply_decode(&result,nonce,wire,64));
 assert(wr_iot_down_query_encode(wire,64,nonce));copyout_fail=1;
 assert(wr_iot_precreated_down_ioctl(&ad,&iot_device,&rq)==-EFAULT&&copyins==3&&copyouts==2);
 assert(!memcmp(&ad,&before,sizeof(ad)));copyout_fail=0;
'''+a
assert s.count(a)==1;s=s.replace(a,b)
with tempfile.TemporaryDirectory(prefix='wr-down-entry-') as d:
 p=Path(d)/'check.c';p.write_text(s);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS actual DOWN ioctl/reply/reference: privilege before copy, fixed ra2, copy-in/out refusal, one observation attempt, adapter unchanged; route uninstalled')
