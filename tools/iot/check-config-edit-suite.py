from pathlib import Path
import argparse
import subprocess
import sys
import tempfile
here=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--native-linux',type=Path)
parser.add_argument('--native-http',type=Path)
args=parser.parse_args()
checks=('check-initial-shutdown-headers.py','check-initial-off-header-staging.py','check-config-edit-pin.py','check-config-edit-lease.py','check-config-edit-route.py',
        'check-config-view-channel.py','check-config-view-endpoint.py','check-config-view-client.py',
        'check-config-view-runtime.py','check-http-view-json.py','check-classic-config-preparation.py',
        'check-save-transport.py','check-config-save-server.py','check-save-route.py',
        'check-status-core.py','check-status-endpoint.py','check-rc-runtime.py',
        'check-rc-scheduler-composition.py','check-rc-view-scheduling.py','check-save-startup.py')
for name in checks:
 subprocess.run([sys.executable,'-B',str(here/name)],check=True,timeout=90)
subprocess.run([sys.executable,'-B',str(here/'check-config-runtime-staging.py')]+
               ([str(args.native_linux.resolve())] if args.native_linux else []),check=True,timeout=60)
if args.native_http:
 subprocess.run([sys.executable,'-B',str(here/'check-http-view-preparation.py'),str(args.native_http.resolve())],check=True,timeout=20)
with tempfile.TemporaryDirectory(prefix='wr-edit-suite-') as directory:
 root=Path(directory)
 for name in ('check-config-edit','check-config-view','check-config-edit-record','check-http-edit-request','check-http-handler'):
  binary=root/name
  subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2',
   '-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(here/(name+'.c')),'-o',str(binary)],check=True)
  subprocess.run([str(binary)],check=True,timeout=15)
for name in ('check-classic-config.js','check-classic-navigation.js'):
 subprocess.run(['node',str(here/name)],check=True,timeout=15)
print('PASS complete edit/view focused host suite; target firmware, assembled Classic and physical acceptance remain required')
