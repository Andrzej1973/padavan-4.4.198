#!/usr/bin/env python3
"""Reuse actual CLOSE-release fixture for the new read-only ARM precondition."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-driver-api-close-release.c').read_text()
prefix=source.split('int main(void)',1)[0]+'#include "physical-stop-prior-close.h"\n'
setup=source[source.index('  int main_dev,device;'):source.index('  switch(fault)')]
body=r'''
int main(void){
 for(unsigned fault=0;fault<13;fault++){
'''+setup+r'''
  assert(wr_iot_driver_close_release_reference(&close,&open,&request,&radio,slots,2,&main_dev,&device,1,&probe,&producer,7));
  assert(!close.active);
  struct wr_iot_physical_stop_request arm={.action=WR_STOP_ARM,.epoch=1,.generation=2,.open_token=3,.closed_serial=4,.nonce={9}};
  if(fault==1)close.active=1;
  if(fault==2)open.active=1;
  if(fault==3)open.poisoned=1;
  if(fault==4)arm.epoch++;
  if(fault==5)arm.generation++;
  if(fault==6)arm.open_token++;
  if(fault==7)arm.closed_serial++;
  if(fault==8)producer.active=1;
  if(fault==9)probe.active=1;
  if(fault==10)close.module_held=1;
  if(fault==11)radio.reset_pending=1;
  if(fault==12)iot->removing=1;
  struct wr_iot_driver_close_owner before=close;
  assert(wr_iot_physical_stop_prior_close(&arm,&close,&open,&radio,slots,2,&main_dev,&device,1,&probe,&producer,7)==(fault==0));
  assert(!memcmp(&before,&close,sizeof(close)));
 }
 puts("PASS prior CLOSE ARM admission: actual released-owner/producer/reference verifier reused read-only,12 identity/lifetime/reset refusals; physical teardown/API binding pending");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='iot-stop-prior-close-') as d:
    unit=Path(d)/'check.c';unit.write_text(prefix+body);binary=Path(d)/'check'
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(unit),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
