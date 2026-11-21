#!/usr/bin/env python3
"""Check isolated installer refusal/immutability using reviewed source snippets."""
from pathlib import Path
import ast,hashlib,json,subprocess,sys,tempfile
here=Path(__file__).resolve().parent
producer=ast.parse((here/'prepare-radio-adapter-candidate.py').read_text())
fresh=next(ast.literal_eval(n.value) for n in producer.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='init' for t in n.targets))
fresh=fresh.replace('wr_iot_radio_transition_init(&pAd->wr_iot_transition);','wr_iot_peer_close_executor_init(&pAd->wr_iot_peer_close_executor);\nwr_iot_radio_transition_init(&pAd->wr_iot_transition);')
files={'include/rtmp.h':'#include "peer-close-executor.h"\nstruct wr_iot_peer_close_executor wr_iot_peer_close_executor;',
       'common/rtmp_init.c':fresh,
       'include/wr-iot-peer-close-executor.inc':(here/'peer-close-executor.inc').read_text(),
       'include/wr-iot-peer-open-dispatch.inc':(here/'peer-open-dispatch.inc').read_text(),
       'include/wr-iot-mbss-recovery-work.inc':' if(ad && (ad->wr_iot_idle_probe.active ||\n     wr_iot_driver_close_blocks_adapter_retirement(&ad->wr_iot_close_owner)))return FALSE;',
       'include/wr-iot-mbss-recovery-join.inc':' if(ad->wr_iot_idle_probe.active ||\n    wr_iot_driver_close_blocks_adapter_retirement(&ad->wr_iot_close_owner))ready=0;'}
with tempfile.TemporaryDirectory(prefix='iot-stop-installer-') as d:
    root=Path(d);source=root/'source';source.mkdir()
    for n,text in files.items():
        f=source/n;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(text)
    before={n:hashlib.sha256((source/n).read_bytes()).hexdigest() for n in files}
    def run(src,out,ok):
        r=subprocess.run([sys.executable,'-B',str(here/'prepare-physical-stop-candidate.py'),str(src),str(out)],capture_output=True,text=True)
        assert (r.returncode==0)==ok,r.stderr
    out=root/'prepared';run(source,out,True)
    report=json.loads(out.with_name(out.name+'-physical-stop.json').read_text())
    assert report['input_sha256']==before
    assert not report['arm_query_endpoint_installed'] and not report['target_compiled']
    assert before=={n:hashlib.sha256((source/n).read_bytes()).hexdigest() for n in files}
    run(out,root/'duplicate',False);assert not (root/'duplicate').exists()
    run(source,out,False)
    main=source/'os/linux/rt_main_dev.c';main.parent.mkdir(parents=True)
    main.write_text('int MainVirtualIF_close(void)\n{\n if (ticket.operation == WR_RADIO_CLOSE) return wr_iot_main_verify_recovery_submit();\n}\n')
    run(source,root/'deferred',False);assert not (root/'deferred').exists()
    (source/'include/link').symlink_to(source/'include/rtmp.h')
    run(source,root/'linked',False);assert not (root/'linked').exists()
print('PASS isolated physical-stop installer: reviewed snippets staged, source hashes unchanged, duplicate/existing/symlink refusals before output; full SDK target pending')
