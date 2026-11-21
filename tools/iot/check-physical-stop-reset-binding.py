"""Actual reset fragment ARM exclusion, host-only kernel context injection."""
from pathlib import Path
import runpy,subprocess,tempfile
here=Path(__file__).resolve().parent
compose=runpy.run_path(str(here/'physical-stop-main-binding.py'))['compose_reset']
# Compose the existing pinned close-executor layer first, then the new ARM gate.
with tempfile.TemporaryDirectory(prefix='wr-stop-reset-predecessor-') as prep:
 root=Path(prep);src=root/'source';(src/'include').mkdir(parents=True)
 for local,target in [('reset-admission.inc','wr-iot-reset-admission.inc'),
                      ('peer-close-executor.h','peer-close-executor.h')]:
  (src/'include'/target).write_bytes((here/local).read_bytes())
 out=root/'executor'
 subprocess.run(['python3',str(here/'prepare-peer-reset-executor.py'),str(src),str(out)],check=True)
 fragment=compose((out/'include/wr-iot-reset-admission.inc').read_text())
try:compose(fragment)
except ValueError:pass
else:raise AssertionError('duplicate reset binding accepted')
s=(here/'check-reset-admission.c').read_text()
s=s.replace('#include "radio-transition.h"','#include "radio-transition.h"\n#include "physical-stop-lifetime.h"\n#include <string.h>\n#include "peer-close-executor.h"')
s=s.replace('int wr_iot_transition_lock;','struct wr_iot_peer_close_executor wr_iot_peer_close_executor;int MacTabLock;struct wr_iot_physical_stop_lifetime wr_iot_physical_lifetime;int wr_iot_transition_lock;')
s=s.replace('#define WR_IOT_RESET_TEST', '#define NdisAcquireSpinLock(l) do{(void)(l);assert(!held);held=1;}while(0)\n#define NdisReleaseSpinLock(l) do{(void)(l);assert(held);held=0;}while(0)\n#define WR_IOT_RESET_TEST')
s=s.replace('#include "reset-admission.inc"',fragment)
anchor=' puts('
a=s.index(anchor)
test=''' {
  struct wr_iot_radio_transition before=a.wr_iot_transition;
  int old_pdma=pdma,old_pse=pse;
  a.wr_iot_physical_lifetime.active=1;
  PDMAResetAndRecovery(&a);PSEResetAndRecovery(&a);
  assert(!memcmp(&before,&a.wr_iot_transition,sizeof(before)));
  assert(pdma==old_pdma&&pse==old_pse&&!held&&!rtnl_held);
  a.wr_iot_transition.reset_pending=WR_RADIO_RESET_PDMA;
  before=a.wr_iot_transition;
  wr_iot_radio_reset_drain(&a);
  assert(!memcmp(&before,&a.wr_iot_transition,sizeof(before)));
  assert(pdma==old_pdma&&!held&&!rtnl_held);
  assert(wr_iot_peer_close_executor_idle(&a.wr_iot_peer_close_executor));
  a.wr_iot_physical_lifetime.active=0;
 }
'''
s=s[:a]+test+s[a:]
with tempfile.TemporaryDirectory(prefix='wr-stop-reset-binding-') as d:
 c=Path(d)/'check.c';c.write_text(s)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(c),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True)
print('PASS actual reset ARM binding: request and pending drain cannot mutate radio under active lifetime; baseline reset regression preserved; target pending')
