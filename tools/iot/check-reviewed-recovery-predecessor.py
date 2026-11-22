"""Check strict join normalization without weakening whole-file source pins."""
import hashlib
import runpy
from pathlib import Path
here=Path(__file__).resolve().parent
normalize=runpy.run_path(str(here/'reviewed-recovery-predecessor.py'))['reviewed_predecessor']
s=(here/'main-recovery-reaper.inc').read_bytes()
a=s.index(b'INT wr_iot_main_recovery_join_complete(');b=s.index(b'\n}',a)+2
body=s[a:b];data=b'prefix\n'+body+b'\nsuffix'
baseline=(here/'main-recovery-join-baseline.inc').read_bytes()
expected=b'prefix\n'+baseline+b'\nsuffix'
assert normalize(data,'os/linux/rt_main_dev.c')==expected
assert normalize(data,'other.c')==data
bad=data.replace(b'dev_put(',b'bad_put(',1)
assert normalize(bad,'os/linux/rt_main_dev.c')==bad
assert normalize(data+data,'os/linux/rt_main_dev.c')==data+data
changed=data.replace(b'prefix',b'foreign')
assert hashlib.sha256(normalize(changed,'os/linux/rt_main_dev.c')).digest()!=hashlib.sha256(expected).digest()
marker=b'VOID wr_iot_main_recovery_reap_work_fn('
start=s.index(marker);end=s.index(b'\n}',start)+2
reaper=s[start:end]
payload=b'prefix\n'+body+b'\n'+reaper+b'\nsuffix'
historical=(here/'main-recovery-reaper-baseline.inc').read_bytes()
assert normalize(payload,'os/linux/rt_main_dev.c')==expected.replace(b'\nsuffix',b'\n'+historical+b'\nsuffix')
changed=reaper.replace(b'flush_work(',b'other_work(',1)
assert normalize(payload.replace(reaper,changed),'os/linux/rt_main_dev.c').endswith(changed+b'\nsuffix')
print('PASS reviewed exact join normalization: current body, mutated body, duplicate, foreign path and surrounding bytes')
