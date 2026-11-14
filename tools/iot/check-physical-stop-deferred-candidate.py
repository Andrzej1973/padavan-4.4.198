"""Check isolated deferred installer with reviewed snippets, not a full SDK."""
from pathlib import Path
import hashlib,json,subprocess,sys,tempfile
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-physical-stop-candidate.py')}
source=(here/'check-physical-stop-candidate.py').read_text()
exec(compile(source[:source.index("with tempfile.TemporaryDirectory(")],'<reviewed fixture setup>','exec'),ns)
files=dict(ns['files'])
files['include/wr-iot-reset-admission.inc']=(here/'reset-admission.inc').read_text()
files['os/linux/rt_main_dev.c']=(here/'main-close-checked.inc').read_text()
files['include/main-open-recovery-owner.h']=(here/'main-open-recovery-owner.h').read_text()
with tempfile.TemporaryDirectory(prefix='wr-stop-deferred-installer-') as d:
 root=Path(d);src=root/'source';src.mkdir()
 for n,text in files.items():
  f=src/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(text)
 hashes=lambda:{n:hashlib.sha256((src/n).read_bytes()).hexdigest() for n in files}
 before=hashes()
 manifest={'production_installed':False,'merged_driver_sha256':before,
 'candidate_driver_sha256':dict(before),'main_physical_close_delegation_layer':{'physical_close_delegated':True}}
 src.with_name(src.name+'.manifest.json').write_text(json.dumps(manifest))
 def run(inp,out,ok):
  r=subprocess.run([sys.executable,'-B',str(here/'prepare-physical-stop-deferred-candidate.py'),str(inp),str(out)],capture_output=True,text=True)
  assert (r.returncode==0)==ok,r.stderr
 out=root/'prepared';run(src,out,True)
 assert hashes()==before
 result=json.loads(out.with_name(out.name+'.manifest.json').read_text())
 assert result['physical_stop_deferred_layer']['main_worker_hook']
 assert not result['physical_stop_deferred_layer']['endpoint_installed']
 assert (out/'include/wr-iot-peer-close-executor.inc').read_bytes()==(src/'include/wr-iot-peer-close-executor.inc').read_bytes()
 assert 'wr_iot_physical_stop_lifetime_capture_main(' in (out/'os/linux/rt_main_dev.c').read_text()
 assert all(hashlib.sha256((out/n).read_bytes()).hexdigest()==h for n,h in result['merged_driver_sha256'].items())
 run(out,root/'duplicate',False);assert not (root/'duplicate').exists()
 (src/'os/linux/rt_main_dev.c').write_text('changed')
 run(src,root/'changed',False);assert not (root/'changed').exists()
print('PASS dormant deferred installer: exact manifest, immutable source/legacy executor, worker hook, refusal before output for drift/duplicate; full SDK/target pending')
