from pathlib import Path
import runpy,subprocess,tempfile
here=Path(__file__).resolve().parent
stop=runpy.run_path(str(here/'physical-stop-dispatch.py'))['compose']
compose=runpy.run_path(str(here/'physical-rebind-dispatch.py'))['compose']
original=(here/'driver-api-closed-entry.inc').read_text();source=stop(original)
changed=compose(source)
for invalid in (original,changed,source.replace('if(!rtnl_is_locked())return -EBUSY;','',1),source.replace('if(!ns_capable(dev_net(dev)->user_ns,CAP_NET_ADMIN))return -EPERM;','',1)):
 try:compose(invalid)
 except ValueError:pass
 else:raise AssertionError('unsafe/duplicate route accepted')
a=changed.index(" if(wire[0]=='W'");b=changed.index('\n',changed.index('return wr_iot_physical_rebind_ioctl',a))+1
code='''#include <assert.h>
static int stops,rebinds;
static int wr_iot_physical_stop_ioctl(void*a,void*d,void*r){(void)a;(void)d;(void)r;stops++;return 7;}
static int wr_iot_physical_rebind_ioctl(void*a,void*d,void*r){(void)a;(void)d;(void)r;rebinds++;return 9;}
static int dispatch(const unsigned char *wire){void *ad=0,*dev=0,*rq=0;
'''+changed[a:b]+'''return 3;}
int main(void){unsigned char w[64]={'W','R','R','B',1};
 assert(dispatch(w)==9&&rebinds==1&&!stops);
 for(unsigned i=0;i<4;i++){w[i]^=1;assert(dispatch(w)==3&&rebinds==1);w[i]^=1;}
 w[1]='P';w[2]='S';w[3]='Q';assert(dispatch(w)==7&&stops==1&&rebinds==1);
 w[3]='R';assert(dispatch(w)==3);return 0;}
'''
with tempfile.TemporaryDirectory(prefix='wr-rebind-route-') as d:
 src=Path(d)/'check.c';out=Path(d)/'check';src.write_text(code)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie',str(src),'-o',str(out)],check=True)
 subprocess.run([str(out)],check=True)
print('PASS exact WRRB route after existing guards/copy; WPSQ retained, foreign/reply fallthrough, missing guard/prerequisite/duplicate refused')
