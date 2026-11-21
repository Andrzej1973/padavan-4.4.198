from pathlib import Path
import argparse
import subprocess
import sys
import tempfile
here=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--native-linux',type=Path)
parser.add_argument('--native-http',type=Path)
parser.add_argument('--native-classic',type=Path)
args=parser.parse_args()
checks=('check-generation-selector-link.py','check-runtime-edit-backend.py','check-generation-saved-boot.py','check-initial-shutdown-headers.py','check-initial-off-header-staging.py','check-config-edit-pin.py','check-config-edit-lease.py','check-config-edit-route.py',
        'check-config-view-channel.py','check-config-view-endpoint.py','check-config-view-client.py',
        'check-config-view-runtime.py','check-http-view-json.py','check-classic-config-preparation.py',
        'check-classic-config-romfs.py',
        'check-save-transport.py','check-config-save-server.py','check-save-route.py',
        'check-status-core.py','check-status-endpoint.py','check-rc-runtime.py',
        'check-rc-scheduler-composition.py','check-rc-view-scheduling.py','check-save-startup.py')
for name in checks:
 command=[sys.executable,'-B',str(here/name)]
 if name=='check-classic-config-romfs.py' and args.native_classic:command.append(str(args.native_classic.resolve()))
 subprocess.run(command,check=True,timeout=90)
subprocess.run([sys.executable,'-B',str(here/'check-config-runtime-staging.py')]+
               ([str(args.native_linux.resolve())] if args.native_linux else []),check=True,timeout=60)
if args.native_http:
 subprocess.run([sys.executable,'-B',str(here/'check-http-view-preparation.py'),str(args.native_http.resolve())],check=True,timeout=20)
with tempfile.TemporaryDirectory(prefix='wr-edit-suite-') as directory:
 root=Path(directory)
 for name in ('check-config-runtime-request','check-config-edit','check-config-view','check-config-edit-record','check-http-edit-request','check-http-handler'):
  binary=root/name
  subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2',
   '-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(here/(name+'.c')),'-o',str(binary)],check=True)
  subprocess.run([str(binary)],check=True,timeout=15)
for name in ('check-classic-config.js','check-classic-navigation.js'):
 subprocess.run(['node',str(here/name)],check=True,timeout=15)
# Modern consumes the same IoT protocol; keep its request/response checks in
# the backend regression gate without installing the candidate into firmware.
modern=here.parent/'webui-preview'
for name in ('check_modern_iot_staging.py','check_modern_iot_native_requests.py',
             'check_modern_iot_native_handlers.py'):
 subprocess.run([sys.executable,'-B',str(modern/name)],check=True,timeout=30)
print('PASS complete edit/view focused host suite including Modern IoT; target firmware, assembled UI and physical acceptance remain required')
