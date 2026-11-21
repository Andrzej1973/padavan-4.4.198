"""Internal execution with actual helper code; owner/netdevice actors injected."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
base=(here/'check-driver-api-open-entry.c').read_text()
prefix=base[:base.index('#include "driver-api-open-entry.inc"')]
# Retain established mocked lifecycle functions; rebind admission delegates to
# the exact same owner-enter actor for this focused execution test.
code=prefix+r'''
#include "physical-stop-wire.h"
static int wr_iot_physical_rebind_request_enter(RTMP_ADAPTER *ad,PNET_DEV dev,
 const struct wr_iot_physical_stop_request *physical,const struct wr_iot_driver_open_request *request)
{assert(physical->action==WR_STOP_RELEASE);return wr_iot_driver_request_enter(ad,dev,request,current);}
#include "physical-rebind-open-entry.inc"
int main(void){
 RTMP_ADAPTER ad={1};device dev={0};
 struct wr_iot_physical_stop_request physical={.action=WR_STOP_RELEASE};
 struct wr_iot_driver_open_request request={.adapter_epoch=1,.device_generation=2};
 strcpy((char *)request.password,"password");
 /* Unused transport mocks belong to the original external-entry fixture. */
 (void)dev_net;(void)ns_capable;(void)copy_from_user;
 assert(wr_iot_physical_rebind_open_execute(0,&dev,&physical,&request)==-EINVAL);
 locked=0;assert(wr_iot_physical_rebind_open_execute(&ad,&dev,&physical,&request)==-EBUSY&&!enters);locked=1;
 dev.running=1;assert(wr_iot_physical_rebind_open_execute(&ad,&dev,&physical,&request)==-EBUSY&&!enters);dev.running=0;
 enter_error=-ESTALE;assert(wr_iot_physical_rebind_open_execute(&ad,&dev,&physical,&request)==-ESTALE&&!opens&&!leaves);
 enter_error=0;open_error=-EBUSY;
 assert(wr_iot_physical_rebind_open_execute(&ad,&dev,&physical,&request)==-EBUSY&&opens==1&&leaves==1&&!waits);
 open_error=0;wait_error=-ETIMEDOUT;
 assert(wr_iot_physical_rebind_open_execute(&ad,&dev,&physical,&request)==-ETIMEDOUT&&leaves==2&&waits==1);
 wait_error=0;leave_ok=0;
 assert(wr_iot_physical_rebind_open_execute(&ad,&dev,&physical,&request)==-EUCLEAN&&leaves==3);
 leave_ok=1;assert(!wr_iot_physical_rebind_open_execute(&ad,&dev,&physical,&request)&&leaves==4);
 assert(!strcmp((char *)request.password,"password"));return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-rebind-open-entry-') as d:
 src=Path(d)/'check.c';out=Path(d)/'check';src.write_text(code)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(src),'-o',str(out)],check=True)
 subprocess.run([str(out)],check=True,timeout=15)
print('PASS actual internal rebind execution: admission refusal no open/leave, dev_open error, beacon timeout, mandatory leave/poison, input preserved; lifecycle actors injected')
