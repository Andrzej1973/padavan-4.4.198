"""Actual direct-free fence with physical ownership and final PID return."""
from pathlib import Path
import runpy,subprocess,tempfile,shutil
here=Path(__file__).resolve().parent
compose=runpy.run_path(str(here/'physical-stop-main-binding.py'))['compose_raw_free']
fragment=compose((here/'raw-recovery-free-fence.inc').read_text())
code=r'''
#include <assert.h>
#include "main-reopen-admission.h"
#include "mbss-recovery-storage.h"
#include "physical-stop-record.h"
#include "physical-stop-lifetime.h"
#include "physical-stop-pin-types.h"
#include "physical-stop-terminal-types.h"
#include "physical-rebind-probe-types.h"
#define WDEV_NUM_MAX 1
#define TRUE 1
#define FALSE 0
#define READ_ONCE(x) (x)
typedef int BOOLEAN;typedef unsigned long ULONG;typedef unsigned int UINT;
struct work_struct {int busy;};
typedef struct {
 int MacTabLock,wr_iot_transition_lock;
 unsigned wr_iot_recovery_storage_live,wr_iot_registration_inflight;
 struct wr_iot_radio_transition wr_iot_transition;
 struct wr_iot_main_recovery_owner wr_iot_main_recovery;
 struct wr_iot_mbss_recovery_owner wr_iot_mbss_recovery[2];
 struct wr_iot_interface_ref wr_iot_interface_refs[2];
 struct work_struct wr_iot_main_recovery_work,wr_iot_aux_family_retry_work;
 struct {struct work_struct work;} wr_iot_main_recovery_reap_work;
 struct {unsigned deferred_owners;} wr_iot_aux_family_retry;
 struct wr_iot_physical_stop_record wr_iot_physical_stop;
 struct wr_iot_physical_stop_lifetime wr_iot_physical_lifetime;
 struct wr_iot_physical_stop_pins wr_iot_physical_pins,wr_iot_physical_pending_pins;
 struct wr_iot_physical_stop_terminal wr_iot_physical_terminal;
 struct wr_iot_physical_rebind_probe wr_iot_physical_rebind_probe;
} RTMP_ADAPTER;
static int held,puts;
struct pid {int refs;};static struct pid identity={2};
#define current ((void *)1)
static struct pid *task_pid(void *task){assert(task==current);return &identity;}
static struct pid *get_pid(struct pid *p){p->refs++;return p;}
static void put_pid(struct pid *p){assert(!held&&p->refs>1);p->refs--;puts++;}
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
static int work_busy(struct work_struct *w){assert(held);return w->busy;}
#include "raw-free-physical.inc"
int main(void){
 RTMP_ADAPTER ad={0};ad.wr_iot_recovery_storage_live=1;
 wr_iot_radio_transition_init(&ad.wr_iot_transition);
 wr_iot_main_recovery_init(&ad.wr_iot_main_recovery);
 for(unsigned i=0;i<2;i++)wr_iot_mbss_recovery_init(&ad.wr_iot_mbss_recovery[i]);
 ad.wr_iot_physical_terminal.owner=&identity;ad.wr_iot_physical_terminal.ready=1;
 ad.wr_iot_physical_rebind_probe.active=1;
 assert(!wr_iot_raw_recovery_free_fence(&ad)&&!puts&&identity.refs==2);
 ad.wr_iot_physical_rebind_probe.active=0;
 ad.wr_iot_physical_lifetime.active=1;
 assert(!wr_iot_raw_recovery_free_fence(&ad)&&!puts&&identity.refs==2);
 ad.wr_iot_physical_lifetime.active=0;ad.wr_iot_physical_pending_pins.module=1;
 assert(!wr_iot_raw_recovery_free_fence(&ad)&&!puts&&identity.refs==2);
 ad.wr_iot_physical_pending_pins.module=0;
 assert(wr_iot_raw_recovery_free_fence(&ad));
 assert(!held&&puts==1&&identity.refs==1&&!ad.wr_iot_physical_terminal.owner);
 assert(wr_iot_raw_recovery_free_fence(&ad)&&puts==1);
 ad.wr_iot_recovery_storage_live=0;ad.wr_iot_physical_terminal.owner=(void *)1;
 assert(wr_iot_raw_recovery_free_fence(&ad)&&puts==1);
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-stop-terminal-free-') as d:
 root=Path(d);(root/'raw-free-physical.inc').write_text(fragment)
 shutil.copyfile(here/'main-reopen-admission.h',root/'wr-iot-main-reopen-admission.h')
 c=root/'check.c';c.write_text(code)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(root),'-I'+str(here),str(c),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True)
print('PASS actual free fence: physical lifetime/partial pins retain, PID cache detached then put once outside locks, cold storage untouched; hardware free acceptance separate')
