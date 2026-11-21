"""Initial storage staging refuses source drift before output creation."""
from pathlib import Path
import tempfile,runpy,hashlib
here=Path(__file__).resolve().parent
prepare=runpy.run_path(str(here/'prepare-physical-initial-storage.py'))['prepare']
raw=runpy.run_path(str(here/'physical-stop-main-binding.py'))['compose_raw_free']((here/'raw-recovery-free-fence.inc').read_text())
with tempfile.TemporaryDirectory(prefix='wr-initial-staging-') as d:
 root=Path(d);src=root/'source';(src/'include').mkdir(parents=True);(src/'common').mkdir()
 (src/'include/rtmp.h').write_text('#include "physical-stop-terminal-types.h"\nstruct wr_iot_physical_stop_terminal wr_iot_physical_terminal;')
 (src/'common/rtmp_init.c').write_text('NdisZeroMemory(&pAd->wr_iot_physical_terminal,sizeof(pAd->wr_iot_physical_terminal));')
 (src/'include/wr-iot-raw-recovery-free-fence.inc').write_text(raw)
 before={str(p.relative_to(src)):hashlib.sha256(p.read_bytes()).hexdigest() for p in src.rglob('*') if p.is_file()}
 out=root/'candidate';report=prepare(src,out)
 assert report['initial_storage_and_retirement_staged'] and not report['endpoint_installed']
 assert before=={str(p.relative_to(src)):hashlib.sha256(p.read_bytes()).hexdigest() for p in src.rglob('*') if p.is_file()}
 try:prepare(out,root/'duplicate')
 except ValueError:pass
 else:raise AssertionError('Duplicate accepted')
 assert not (root/'duplicate').exists()
 (src/'include/rtmp.h').write_text('changed')
 try:prepare(src,root/'broken')
 except ValueError:pass
 else:raise AssertionError('Missing anchor accepted')
 assert not (root/'broken').exists()
print('PASS initial storage candidate staging: source unchanged, helper closure copied, explicit dormant manifest, duplicate/drift refuse before output; synthetic SDK anchors')
