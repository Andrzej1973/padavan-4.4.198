"""Storage transform anchor closure and refusal; candidate install still separate."""
from pathlib import Path
import runpy
here=Path(__file__).resolve().parent
compose=runpy.run_path(str(here/'physical-initial-storage.py'))['compose']
raw_transform=runpy.run_path(str(here/'physical-stop-main-binding.py'))['compose_raw_free']
raw=raw_transform((here/'raw-recovery-free-fence.inc').read_text())
header='#include "physical-stop-terminal-types.h"\nstruct wr_iot_physical_stop_terminal wr_iot_physical_terminal;'
init='NdisZeroMemory(&pAd->wr_iot_physical_terminal,sizeof(pAd->wr_iot_physical_terminal));'
h,i,r=compose(header,init,raw)
assert h.count('struct wr_iot_physical_initial_record wr_iot_physical_initial;')==1
assert h.count('struct wr_iot_physical_initial_terminal wr_iot_physical_initial_terminal;')==1
assert 'NdisZeroMemory(&pAd->wr_iot_physical_initial,' in i
assert '!ad->wr_iot_physical_initial.task' in r
assert 'ad->wr_iot_physical_initial_terminal.ready' in r
assert r.index('RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);')<r.index('wr_iot_physical_initial_terminal_clear(&initial)')
for values in [(h,i,r),(header,init,raw.replace('ready=ad->wr_iot_physical_stop.phase==WR_PHYS_STOP_IDLE&&','changed')),(header.replace('physical-stop-terminal-types.h','missing.h'),init,raw)]:
 try:compose(*values)
 except ValueError:pass
 else:raise AssertionError('Changed/duplicate storage accepted')
print('PASS initial storage transform: actual raw-free composition, field/init/retirement/PID-drop ordering anchors and duplicate/drift refusal; not compiled or installed')
