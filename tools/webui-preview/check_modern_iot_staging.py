#!/usr/bin/env python3
"""Check candidate staging refusal and execute its generated Modern controller."""
import json,runpy,subprocess,tempfile
from pathlib import Path
here=Path(__file__).resolve().parent
prepare=runpy.run_path(str(here/'prepare-modern-iot.py'))['prepare']
with tempfile.TemporaryDirectory(prefix='modern-iot-') as td:
 root=Path(td);modern=root/'trunk/user/www/modern';modern.parent.mkdir(parents=True)
 http=root/'trunk/user/httpd/web_ex.c';http.parent.mkdir(parents=True)
 (modern.parent/'Makefile').write_text('romfs:\n\tcp -R $(WEBUI_NAME) $(ROMFS_DIR)/www\n')
 routes=[('token','NULL','wr_iot_http_token_output'),('view','wr_iot_http_apply_input','wr_iot_http_view_output'),('result','NULL','wr_iot_http_result_output')]
 routes += [('edit_'+s,'wr_iot_http_apply_input','wr_iot_http_edit_'+s+'_output') for s in ('ram','auto','save','runtime')]
 route_rows='\n'.join('{ "wr_iot_'+n+'.cgi", "application/json", no_cache_IE, '+i+', '+o+', 1 },' for n,i,o in routes)
 http.write_text('struct mime_handler mime_handlers[] = {\n'+route_rows+'\n};\n')
 subprocess.run(['python3',str(here/'prepare-production.py'),str(root)],check=True)
 text=http.read_text()
 baseline={p.name:p.read_bytes() for p in modern.iterdir()}
 metadata={'board':'WR1200JS',**{k:True for k in ('edit_startup_attempt_prepared','view_startup_attempt_prepared','native_capabilities_verified','http_view_bound','http_edit_bound','http_runtime_toggle_bound')}}
 meta=root/'iot-edit-view-source.json';meta.write_text(json.dumps(metadata))
 for route,_,_ in routes:
  http.write_text(text.replace('wr_iot_'+route+'.cgi','missing.cgi',1))
  before={p:p.read_bytes() for p in root.rglob('*') if p.is_file()}
  try:prepare(root)
  except ValueError:pass
  else:raise AssertionError('missing route accepted')
  assert before=={p:p.read_bytes() for p in root.rglob('*') if p.is_file()}
 http.write_text(text);prepare(root)
 assert (modern/'index.html').read_text().index('src="/modern/modern-iot.js"')<(modern/'index.html').read_text().index('src="/modern/wifi.js"')
 assert 'window.wrModernIot.render(panel)' in (modern/'wifi.js').read_text()
 before={p:p.read_bytes() for p in root.rglob('*') if p.is_file()}
 try:prepare(root)
 except ValueError:pass
 else:raise AssertionError('duplicate staging accepted')
 assert before=={p:p.read_bytes() for p in root.rglob('*') if p.is_file()}
 stage=runpy.run_path(str(here/'stage-modern-iot-romfs.py'))['stage']
 candidate=root/'linked';(candidate/'modern').mkdir(parents=True)
 (candidate/'modern-iot-candidate.json').write_bytes((root/'modern-iot-candidate.json').read_bytes())
 romfs=root/'romfs';installed=romfs/'www/modern';installed.mkdir(parents=True)
 binary=romfs/'usr/sbin/httpd';binary.parent.mkdir(parents=True)
 for name in ('index.html','wifi.js','modern-iot.js'):
  (candidate/'modern'/name).write_bytes((modern/name).read_bytes())
 for name,data in baseline.items():
  (installed/name).write_bytes(data)
 report=root/'isolated-modern-iot.json'
 linked=candidate/'httpd';linked.write_bytes(b'fixture\0modern/modern-iot.js\0')
 binary.write_bytes(b'other binary')
 try:stage(romfs,candidate,report)
 except ValueError:pass
 else:raise AssertionError('mismatched httpd accepted')
 binary.write_bytes(linked.read_bytes())
 js=candidate/'modern/modern-iot.js';data=js.read_bytes();js.write_bytes(data+b'changed')
 try:stage(romfs,candidate,report)
 except ValueError:pass
 else:raise AssertionError('modified Modern asset accepted')
 assert not report.exists() and not (installed/'modern-iot.js').exists()
 assert {p.name:p.read_bytes() for p in installed.iterdir()}==baseline
 js.write_bytes(data);stage(romfs,candidate,report)
 assert {p.name:p.read_bytes() for p in installed.iterdir()}=={p.name:p.read_bytes() for p in modern.iterdir()}
 assert json.loads(report.read_text())['trx_verified'] is False
 subprocess.run(['node',str(here/'check_modern_iot.js'),str(modern/'modern-iot.js')],check=True)
 subprocess.run(['node',str(here/'check_modern_iot_timeout.js'),str(modern/'modern-iot.js')],check=True)
print('PASS production Modern shell to isolated IoT ROMFS staging: seven route gates, script order, exact httpd/assets, tamper and duplicate refusal; synthetic target binary')
