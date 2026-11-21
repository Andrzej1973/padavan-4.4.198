from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile
here=Path(__file__).resolve().parent
native=Path(sys.argv[1])
with tempfile.TemporaryDirectory(prefix='wr-http-view-stage-') as directory:
 root=Path(directory);http=root/'trunk/user/httpd';http.mkdir(parents=True)
 for name in ('httpd.c','web_ex.c'):(http/name).write_bytes((native/name).read_bytes())
 subprocess.run([sys.executable,str(here/'prepare-http.py'),str(root)],check=True)
 fixture=root/'metadata.c';binary=root/'metadata'
 subprocess.run([sys.executable,str(here/'check-http-source.py'),str(root),str(fixture)],check=True)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2',str(fixture),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=5)
 for name in ('http-view-request.h','config-view-json.h','config-view-client.h','config-view.h'):
  assert (http/'wr-iot'/name).read_bytes()==(here/name).read_bytes()
 def digests():
  return {str(path.relative_to(http)):hashlib.sha256(path.read_bytes()).hexdigest() for path in http.rglob('*') if path.is_file()}
 before=digests()
 repeated=subprocess.run([sys.executable,str(here/'prepare-http.py'),str(root)],capture_output=True,text=True)
 assert repeated.returncode!=0 and digests()==before
print('PASS actual pinned HTTP source preparation: exact authenticated board-scoped view POST, executable metadata capture, complete helper headers and repeated-install refusal without writes; no target/HTTP runtime acceptance')
