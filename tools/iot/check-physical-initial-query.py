"""Execute actual read-only initial QUERY alongside real completion fixture."""
from pathlib import Path
import subprocess,tempfile,shutil
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-physical-initial-completion.py')}
s=(here/'check-physical-initial-completion.py').read_text()
exec(compile(s[:s.index('\nwith tempfile.TemporaryDirectory(')],'<completion fixture>','exec'),ns)
code=ns['code'].replace('#include "physical-initial-main-completion.inc"',
 '#include "physical-initial-main-completion.inc"\nstatic void *current;\n#include "physical-initial-query.inc"')
anchor=' assert(!wr_iot_physical_initial_main_complete(&ad,&main_dev,attempt.serial));'
test=r'''
 {unsigned char wire[64];struct wr_iot_physical_initial_response decoded;
  struct wr_iot_physical_initial_request q=attempt.request;
  unsigned prior=ad.wr_iot_physical_initial.status;
  q.action=WR_STOP_QUERY;q.attempt=attempt.serial;current=&task;
  assert(!wr_iot_physical_initial_query_owned(&ad,&main_dev,&q,wire,64));
  assert(wr_iot_physical_initial_decode(&decoded,wire,64,1));
  assert(decoded.status==prior);
  for(unsigned fault=0;fault<5;fault++){
   RTMP_ADAPTER bad=ad;struct wr_iot_physical_initial_request wrong=q;
   switch(fault){case 0:wrong.nonce[0]^=1;break;
    case 1:wrong.attempt++;break;case 2:bad.wr_iot_physical_pins.module=0;break;
    case 3:bad.wr_iot_physical_lifetime.serial++;break;
    case 4:current=&main_dev;break;}
   memset(wire,0xff,64);
   assert(wr_iot_physical_initial_query_owned(&bad,&main_dev,&wrong,wire,64)==-EAGAIN);
   for(unsigned j=0;j<64;j++)assert(!wire[j]);
   assert(bad.wr_iot_physical_initial.status==prior&&!locked);current=&task;
  }
  rtnl=0;assert(wr_iot_physical_initial_query_owned(&ad,&main_dev,&q,wire,64)==-EBUSY);rtnl=1;
 }
'''
assert code.count(anchor)==2
code=code.replace(anchor,test+anchor)
with tempfile.TemporaryDirectory(prefix='wr-initial-query-') as d:
 root=Path(d)
 for p in here.glob('*.h'):shutil.copy2(p,root/p.name)
 for name in ('radio-transition.h','radio-transition-api.h'):
  p=root/name;p.write_text(p.read_text().replace('virtual_down_stage,virtual_up_stage;','virtual_down_stage,virtual_up_stage,mt_radio_off_stage;'))
 unit=root/'check.c';unit.write_text(code)
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True,timeout=15)
print('PASS actual initial QUERY: RUNNING/COMPLETE readback, foreign task/nonce/attempt/lifetime/pins refusal, zero reply on refusal, no state changes; endpoint not installed')
