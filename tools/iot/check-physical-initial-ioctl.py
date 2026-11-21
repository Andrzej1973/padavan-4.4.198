"""Exercise actual INITIAL_OFF ioctl with full provider and user-copy actors."""
from pathlib import Path
import subprocess,tempfile,shutil
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-physical-initial-handler.py')}
s=(here/'check-physical-initial-handler.py').read_text()
exec(compile(s[:s.index('\nwith tempfile.TemporaryDirectory(')],'<provider fixture>','exec'),ns)
code=ns['code']
hooks=r'''
struct ifreq {void *ifr_data;};
struct fixture_net {void *user_ns;};static struct fixture_net fixture_net;
static int capability=1,copy_in_fail,copy_out_fail;static unsigned copies_in,copies_out;
#define CAP_NET_ADMIN 12
static struct fixture_net *dev_net(PNET_DEV dev){assert(dev);return &fixture_net;}
static int ns_capable(void *ns,int cap){assert(ns==fixture_net.user_ns&&cap==CAP_NET_ADMIN);return capability;}
static int copy_from_user(void *dst,const void *src,unsigned size){
 assert(!locked&&size==64);copies_in++;if(copy_in_fail)return 1;memcpy(dst,src,size);return 0;
}
static int copy_to_user(void *dst,const void *src,unsigned size){
 assert(!locked&&size==64);copies_out++;if(copy_out_fail)return 1;memcpy(dst,src,size);return 0;
}
#include "physical-initial-ioctl.inc"
static int through_ioctl(RTMP_ADAPTER *ad,PNET_DEV dev,
 const struct wr_iot_physical_initial_request *q,unsigned char *output,unsigned length){
 unsigned char user_wire[64];struct ifreq rq={user_wire};int result;
 assert(length==64&&wr_iot_physical_initial_encode(user_wire,64,q,0));
 result=wr_iot_physical_initial_ioctl(ad,dev,&rq);
 if(!result)memcpy(output,user_wire,64);
 return result;
}
'''
code=code.replace('#include "physical-initial-handler.inc"','#include "physical-initial-handler.inc"\n'+hooks,1)
code=code.replace('wr_iot_physical_initial_handle(&full,','through_ioctl(&full,').replace('wr_iot_physical_initial_handle(&ad,','through_ioctl(&ad,')
a=' fail_module=1;\n assert(through_ioctl(&full,'
b=r''' {
 unsigned before=copies_in;struct ifreq rq={output};
 capability=0;
 assert(through_ioctl(&full,&main_dev,&q,output,64)==-EPERM);
 assert(copies_in==before&&!full.wr_iot_physical_lifetime.active);
 capability=1;rtnl=0;
 assert(through_ioctl(&full,&main_dev,&q,output,64)==-EBUSY);rtnl=1;
 assert(copies_in==before);
 copy_in_fail=1;
 assert(through_ioctl(&full,&main_dev,&q,output,64)==-EFAULT);copy_in_fail=0;
 memset(output,0,64);
 assert(wr_iot_physical_initial_ioctl(&full,&main_dev,&rq)==-EINVAL);
 assert(!full.wr_iot_physical_lifetime.active&&modules==1);
 }
 fail_module=1;
 assert(through_ioctl(&full,'''
assert a in code;code=code.replace(a,b,1)
a=' fail_module=0;\n assert(!through_ioctl(&full,&main_dev,&q,output,64));'
b=r''' fail_module=0;
 copy_out_fail=1;
 assert(through_ioctl(&full,&main_dev,&q,output,64)==-EFAULT);
 assert(full.wr_iot_physical_initial.serial==1&&modules==2&&tasks==2&&devices==2);
 copy_out_fail=0;
 assert(!through_ioctl(&full,&main_dev,&q,output,64));'''
assert a in code;code=code.replace(a,b,1)
a=' assert(!through_ioctl(&full,&main_dev,&q,output,64));\n assert(wr_iot_physical_initial_decode(&decoded,output,64,1)&&decoded.status==WR_STOP_CANCELLED);'
b=r''' copy_out_fail=1;
 assert(through_ioctl(&full,&main_dev,&q,output,64)==-EFAULT);
 assert(modules==1&&tasks==1&&devices==1&&full.wr_iot_physical_initial_terminal.ready);
 copy_out_fail=0;
 assert(!through_ioctl(&full,&main_dev,&q,output,64));
 assert(wr_iot_physical_initial_decode(&decoded,output,64,1)&&decoded.status==WR_STOP_CANCELLED);'''
assert a in code;code=code.replace(a,b,1)
with tempfile.TemporaryDirectory(prefix='wr-initial-ioctl-') as d:
 root=Path(d)
 for p in here.glob('*.h'):
  text=p.read_text()
  if p.name in ('radio-transition.h','radio-transition-api.h'):
   text=text.replace('virtual_down_stage,virtual_up_stage;','virtual_down_stage,virtual_up_stage,mt_radio_off_stage;')
  (root/p.name).write_text(text)
 unit=root/'check.c';unit.write_text(code)
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True,timeout=15)
print('PASS actual INITIAL_OFF ioctl/provider: capability/RTNL/malformed/copy-in refusal; lost ARM/CANCEL replies retain exact retry, no extra refs; checked RELEASE through ioctl; dispatch/target uninstalled')
