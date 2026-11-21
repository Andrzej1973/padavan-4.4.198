"""Actual common dispatch validates privilege and single-copy DOWN route."""
from pathlib import Path
import runpy,subprocess,tempfile
here=Path(__file__).resolve().parent
base=runpy.run_path(str(here/'release-dispatch-composition.py'))['compose']
compose=runpy.run_path(str(here/'down-dispatch-composition.py'))['compose']
prepared=base((here/'driver-api-closed-entry.inc').read_text())
generated=compose(prepared)
assert generated.count('copy_from_user(wire,rq->ifr_data,sizeof(wire))')==1
assert generated.index('CAP_NET_ADMIN')<generated.index('if(wire[4]==WR_IOT_DOWN_QUERY)')
for changed in [generated,prepared.replace('if(!rtnl_is_locked())return -EBUSY;',''),prepared.replace('if(copy_from_user(wire,rq->ifr_data,sizeof(wire)))return -EFAULT;','')]:
 try:compose(changed)
 except ValueError:pass
 else:raise AssertionError('unsafe entry accepted')
# Reuse actual existing common-dispatch C fixture; inject only observation.
ns={'__file__':str(here/'check-release-dispatch-composition.py')}
source=(here/'check-release-dispatch-composition.py').read_text()
source=source.replace("generated = compose(original)","generated = compose(original)\ngenerated = __import__('runpy').run_path(str(here/'down-dispatch-composition.py'))['compose'](generated)")
source=source.replace("binding = r'''", "binding = r'''\n#include \"precreated-down-wire.h\"\nstatic int wr_iot_precreated_down_reply(RTMP_ADAPTER *ad,PNET_DEV dev,const unsigned char*q,unsigned int n,unsigned char*r){unsigned char id[16];(void)ad;(void)dev;assert(rtnl&&permitted&&copies_in);if(!wr_iot_down_query_decode(id,q,n))return -EINVAL;return wr_iot_down_reply_encode(r,n,id,1,2,7)?0:-EINVAL;}\n")
source=source.replace("generated = generated.replace('#include \"driver-api-close-release-binding.inc\"', '')", "generated = generated.replace('#include \"precreated-down-reply.inc\"', '')\ngenerated = generated.replace('#include \"driver-api-close-release-binding.inc\"', '')")
# Add DOWN roundtrip ahead of existing per-fault release cases.
a=' for(unsigned fault=0;fault<11;fault++){'
b=''' {
  struct device main_dev={1},iot={0};struct adapter ad={.mt7603=1,.net_dev=&main_dev,.ApCfg.BssidNum=3};
  ad.ApCfg.MBSSID[2].wdev.if_dev=&iot;
  unsigned char id[16]={1},wire[64];struct ifreq rq={wire};struct wr_iot_down_result out;
  rtnl=permitted=1;assert(wr_iot_down_query_encode(wire,64,id));
  assert(!wr_iot_driver_closed_ioctl(&ad,&iot,&rq));
  assert(wr_iot_down_reply_decode(&out,id,wire,64)&&out.main_close_serial==7);
 }
'''+a
assert a in source
source=source.replace(a,b)
exec(compile(source,str(here/'check-release-dispatch-composition.py'),'exec'),ns)
print('PASS proposed DOWN dispatcher: guarded single copy-in, typed reply roundtrip, changed boundaries refuse; observation actor, route not applied')
