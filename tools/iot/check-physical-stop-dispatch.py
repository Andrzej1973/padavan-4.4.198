"""Existing closed ioctl privilege boundary and distinct request discriminator."""
from pathlib import Path
import runpy,subprocess,tempfile
here=Path(__file__).resolve().parent
compose=runpy.run_path(str(here/'physical-stop-dispatch.py'))['compose']
source=(here/'driver-api-closed-entry.inc').read_text()
changed=compose(source)
try:compose(changed)
except ValueError:pass
else:raise AssertionError('duplicate dispatch accepted')
for guard in ('if(!rtnl_is_locked())return -EBUSY;',
 'if(!ns_capable(dev_net(dev)->user_ns,CAP_NET_ADMIN))return -EPERM;',
 'if(!IS_MT7603(ad))return -EOPNOTSUPP;'):
 try:compose(source.replace(guard,'',1))
 except ValueError:pass
 else:raise AssertionError('missing privilege guard accepted')
a=changed.index(" if(wire[0]=='W'");b=changed.index('\n',changed.index('return wr_iot_physical_stop_ioctl',a))+1
route=changed[a:b]
code='''#include <assert.h>
static int calls;
static int wr_iot_physical_stop_ioctl(void*a,void*d,void*r){(void)a;(void)d;(void)r;calls++;return 7;}
static int dispatch(const unsigned char *wire){void *ad=0,*dev=0,*rq=0;
'''+route+'''return 3;}
int main(void){unsigned char wire[64]={'W','P','S','Q',1};
 assert(dispatch(wire)==7&&calls==1);
 for(unsigned i=0;i<4;i++){wire[i]^=1;assert(dispatch(wire)==3&&calls==1);wire[i]^=1;}
 wire[3]='R';assert(dispatch(wire)==3&&calls==1);
 return 0;}
'''
with tempfile.TemporaryDirectory(prefix='wr-stop-dispatch-') as d:
 c=Path(d)/'check.c';c.write_text(code)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie',str(c),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True)
print('PASS existing closed ioctl route: guards precede copy/dispatch, WPSQ exact discriminator, reply/foreign headers fall through; wrapper/handler separately tested')
