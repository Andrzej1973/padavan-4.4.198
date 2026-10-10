#!/usr/bin/env python3
"""Synthetic negative tests for the image gate, not firmware proof."""
import subprocess,sys,tempfile
from pathlib import Path
local=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
 root=Path(directory);www=root/'www';www.mkdir();(root/'usr/sbin').mkdir(parents=True)
 page='<section id="wr-connected-devices"></section><section id="wr-roaming-history"></section><iframe id="statusframe"></iframe>'
 for name in ('classify','refresh','homepage','roaming','roaming-view','boot'):
  target='wr-device-'+name+'.js';(www/target).write_bytes((local/(name+'.js')).read_bytes());page+='<script src="/'+target+'"></script>'
 (www/'wr-device-homepage.css').write_bytes((local/'homepage.css').read_bytes());page+='<link href="/wr-device-homepage.css">';(www/'index.asp').write_text(page)
 markers=[b'wr_devices.json',b'wr_roaming.json',b'/var/run/wr-device-observer/actions',b'/var/run/wr-band-steering.lock',b'/usr/sbin/wr-band-steering',b'monitoringGap',b'interruptions',b'ioctl_accepted',b'ioctl_failed',b'driver_ack',b'remove_candidate']
 daemon=root/'usr/sbin/httpd'
 def check(ok):
  result=subprocess.run([sys.executable,str(local/'verify-ui-image.py'),str(root)],capture_output=True)
  assert (result.returncode==0)==ok,result.stderr.decode()
 daemon.write_bytes(b'\0'.join(markers));check(True)
 for missing in markers:
  daemon.write_bytes(b'\0'.join(m for m in markers if m!=missing));check(False)
 daemon.write_bytes(b'\0'.join(markers));(www/'wr-device-roaming-view.js').write_text('obsolete');check(False)
print('PASS image gate rejects every missing linked observer marker and obsolete action UI; synthetic fixture only')
