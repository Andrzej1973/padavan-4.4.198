#!/usr/bin/env python3
"""Check candidate staging refusal and execute its generated Modern controller."""
import json,runpy,subprocess,tempfile
from pathlib import Path
here=Path(__file__).resolve().parent
prepare=runpy.run_path(str(here/'prepare-modern-iot.py'))['prepare']
with tempfile.TemporaryDirectory(prefix='modern-iot-') as td:
 root=Path(td);modern=root/'trunk/user/www/modern';modern.mkdir(parents=True)
 http=root/'trunk/user/httpd/web_ex.c';http.parent.mkdir(parents=True)
 routes=[('token','NULL','wr_iot_http_token_output'),('view','wr_iot_http_apply_input','wr_iot_http_view_output'),('result','NULL','wr_iot_http_result_output')]
 routes += [('edit_'+s,'wr_iot_http_apply_input','wr_iot_http_edit_'+s+'_output') for s in ('ram','auto','save','runtime')]
 text='\n'.join('{ "wr_iot_'+n+'.cgi", "application/json", no_cache_IE, '+i+', '+o+', 1 }' for n,i,o in routes)
 text+='\n{ "modern/wifi.js", "text/javascript", no_cache_IE, NULL, do_file, 1 },'
 http.write_text(text)
 (modern/'wifi.js').write_text((here/'public/wifi.js').read_text())
 (modern/'index.html').write_text('<script src="/modern/wifi.js" defer></script>')
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
 assert (modern/'index.html').read_text().index('modern-iot.js')<(modern/'index.html').read_text().index('wifi.js')
 assert 'window.wrModernIot.render(panel)' in (modern/'wifi.js').read_text()
 before={p:p.read_bytes() for p in root.rglob('*') if p.is_file()}
 try:prepare(root)
 except ValueError:pass
 else:raise AssertionError('duplicate staging accepted')
 assert before=={p:p.read_bytes() for p in root.rglob('*') if p.is_file()}
 subprocess.run(['node',str(here/'check_modern_iot.js'),str(modern/'modern-iot.js')],check=True)
 subprocess.run(['node',str(here/'check_modern_iot_timeout.js'),str(modern/'modern-iot.js')],check=True)
print('PASS Modern IoT staging: all seven authenticated routes required, script ordering, renderer hook, missing-route and duplicate refusal without writes; isolated fixture only')
