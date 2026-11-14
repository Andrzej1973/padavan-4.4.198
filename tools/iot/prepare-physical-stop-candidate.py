#!/usr/bin/env python3
"""Stage dormant physical-stop storage/hooks in a separate driver candidate.

No endpoint is supplied. Do not expose this until arm/lifetime/reset bindings
are complete. Never edits the source tree or installs into production.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:
    p.error('new separate output required')
if any(f.is_symlink() for f in src.rglob('*')):
    p.error('driver candidate symlinks are unsupported')
main_source=src/'os/linux/rt_main_dev.c'
if main_source.is_file():
    main_text=main_source.read_text()
    marker='int MainVirtualIF_close('
    if marker in main_text:
        start=main_text.index(marker);end=main_text.index('\n}',start)+2
        close=main_text[start:end]
        if 'ticket.operation == WR_RADIO_CLOSE' in close and 'wr_iot_main_verify_recovery_submit' in close:
            p.error('deferred checked main-close requires recovery-owner/ticket binding; legacy-only physical hooks are unsupported')
here=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('physical',here/'physical-stop-executor.py')
helpers=importlib.util.module_from_spec(spec);spec.loader.exec_module(helpers)
names=('include/rtmp.h','common/rtmp_init.c','include/wr-iot-peer-close-executor.inc',
       'include/wr-iot-peer-open-dispatch.inc','include/wr-iot-mbss-recovery-work.inc',
       'include/wr-iot-mbss-recovery-join.inc')
texts={n:(src/n).read_text() for n in names}
# Do not silently replace downstream changes in the close executor.
if texts[names[2]]!=(here/'peer-close-executor.inc').read_text():
    p.error('unreviewed close executor predecessor')
try:
    texts[names[0]],texts[names[1]]=helpers.compose_adapter(texts[names[0]],texts[names[1]])
    texts[names[2]]=helpers.compose(texts[names[2]])
    texts[names[3]]=helpers.compose_open_dispatch(texts[names[3]])
    texts[names[4]],texts[names[5]]=helpers.compose_retirement(texts[names[4]],texts[names[5]])
except ValueError as e:p.error(str(e))
for n in ('physical-stop-record.h','physical-stop-lifetime.h','physical-stop-pin-types.h'):
    if (src/'include'/n).exists():p.error('physical-stop header already present: '+n)
# Validate every transformation before creating the output.
shutil.copytree(src,out,symlinks=True)
for n,text in texts.items():(out/n).write_text(text)
for n in ('physical-stop-record.h','physical-stop-lifetime.h','physical-stop-pin-types.h'):
    shutil.copyfile(here/n,out/'include'/n)
hashes=lambda root:{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest()
                    for f in root.rglob('*') if f.is_file() and not f.is_symlink()}
report={'input_sha256':hashes(src),'output_sha256':hashes(out),
        'executor_binding_scope':'synchronous legacy model only; deferred checked physical close unsupported',
        'storage_and_executor_staged':True,'arm_query_endpoint_installed':False,
        'kernel_pin_binding_installed':False,'reset_open_admission_complete':False,
        'production_installed':False,'target_compiled':False,'runtime_verified':False}
out.with_name(out.name+'-physical-stop.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS dormant physical-stop candidate staged; arm/query, pins and reset admission remain unbound')
