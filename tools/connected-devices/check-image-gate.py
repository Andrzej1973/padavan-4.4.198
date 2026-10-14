#!/usr/bin/env python3
"""Synthetic negative tests for the image gate, not firmware proof."""
import subprocess,sys,uuid,shutil,json
from contextlib import contextmanager
from pathlib import Path
local=Path(__file__).resolve().parent
@contextmanager
def fixture_directory():
 directory=Path.cwd()/('image-gate-'+uuid.uuid4().hex)
 directory.mkdir()
 try:
  yield directory
 finally:
  assert directory.resolve().parent==Path.cwd().resolve()
  shutil.rmtree(directory)
with fixture_directory() as directory:
 root=Path(directory);www=root/'www';www.mkdir();(root/'usr/sbin').mkdir(parents=True)
 assert root.resolve().parent==Path.cwd().resolve()
 keys=('state-current','state-stale','state-unavailable','state-updating','state-paused','state-stopped','last-observations','source-networkmap','source-radio','source-initialization')
 keys+=('title','description','retry','source-time-unavailable','empty','no-match','source-time')
 keys+=('column-device','column-connection','column-category','column-confidence','connection-associated','connection-last','connection-seen','connection-unknown','confidence-unknown','confidence-possible','confidence-high','confidence-manufacturer','confidence-user','unnamed','classification-none','last-evidence')
 keys+=('network-primary','network-guest','network-iot','network-unknown','category-all','category-unknown','category-tv','notice-truncated','notice-invalid','evidence-android-host','evidence-android-dhcp','evidence-windows-host','evidence-windows-dhcp','evidence-tv-host','evidence-conflict','evidence-manual','evidence-manufacturer')
 rssi_keys=tuple(json.loads((local/'rssi-labels.json').read_text(encoding='utf-8')))
 keys+=rssi_keys
 history_keys=tuple(json.loads((local/'history-labels.json').read_text(encoding='utf-8')))
 keys+=history_keys
 attributes=''.join(' data-wr-'+key+'="<#WRDeviceStatus_'+key+'#>"' for key in keys)
 state_attributes=''.join(' data-wr-'+key+'="<#WRDeviceStatus_'+key+'#>"' for key in keys[:7])
 rssi_attributes=''.join(' data-wr-'+key+'="<#WRDeviceStatus_'+key+'#>"' for key in rssi_keys)
 history_attributes=''.join(' data-wr-'+key+'="<#WRDeviceStatus_'+key+'#>"' for key in history_keys)
 page='<section id="wr-connected-devices"'+attributes+'></section><section id="wr-roaming-history"'+state_attributes+history_attributes+'></section><section id="wr-rssi-history"'+state_attributes+rssi_attributes+'></section><iframe id="statusframe"></iframe>'
 dictionary='\n'+''.join('WRDeviceStatus_'+key+'=fixture label\n' for key in keys)
 for locale in ('EN','UK','RU'):(www/(locale+'.dict')).write_text(dictionary,encoding='utf-8')
 for name in ('classify','refresh','homepage','roaming','roaming-view','rssi','rssi-view','boot'):
  target='wr-device-'+name+'.js';(www/target).write_bytes((local/(name+'.js')).read_bytes());page+='<script src="/'+target+'"></script>'
 (www/'wr-device-homepage.css').write_bytes((local/'homepage.css').read_bytes());page+='<link href="/wr-device-homepage.css">';(www/'index.asp').write_text(page)
 markers=[b'wr_devices.json',b'wr_roaming.json',b'wr_rssi.json',b'/var/run/wr-device-observer/actions',b'/var/run/wr-band-steering.lock',b'/usr/sbin/wr-band-steering',b'monitoringGap',b'interruptions',b'ioctl_accepted',b'ioctl_failed',b'driver_ack',b'remove_candidate']
 daemon=root/'usr/sbin/httpd'
 def check(ok):
  result=subprocess.run([sys.executable,str(local/'verify-ui-image.py'),str(root)],capture_output=True)
  assert (result.returncode==0)==ok,result.stderr.decode()
 daemon.write_bytes(b'\0'.join(markers));check(True)
 for locale in ('EN','UK','RU'):
  target=www/(locale+'.dict')
  for key in keys:
   target.write_text(dictionary.replace('WRDeviceStatus_'+key+'=fixture label\n',''),encoding='utf-8');check(False)
  key=keys[0]
  for replacement in ('', '   ', '<#unresolved#>'):
   target.write_text(dictionary.replace('WRDeviceStatus_'+key+'=fixture label', 'WRDeviceStatus_'+key+'='+replacement),encoding='utf-8');check(False)
  target.write_text(dictionary+'WRDeviceStatus_'+key+'=duplicate\n',encoding='utf-8');check(False)
  target.write_text(dictionary,encoding='utf-8');check(True)
 for missing in markers:
  daemon.write_bytes(b'\0'.join(m for m in markers if m!=missing));check(False)
 daemon.write_bytes(b'\0'.join(markers))
 for name in ('rssi','rssi-view'):
  asset=www/('wr-device-'+name+'.js');original=asset.read_bytes()
  asset.unlink();check(False);asset.write_bytes(original);check(True)
 daemon.write_bytes(b'\0'.join(markers));(www/'wr-device-roaming-view.js').write_text('obsolete');check(False)
print('PASS image gate rejects every missing linked observer marker and obsolete action UI; synthetic fixture only')
