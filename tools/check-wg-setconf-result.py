#!/usr/bin/env python3
"""Exercise exact post-setconf result blocks with synthetic utilities only."""
from pathlib import Path
import os
import subprocess
import tempfile
with tempfile.TemporaryDirectory(prefix='wg-setconf-') as temp:
 root=Path(temp)
 for name in ['wgc.sh','wgs.sh']:
  text=(Path(__file__).resolve().parent.parent/'overlay/padavan-4.4/trunk/user/amneziawg'/name).read_text()
  start=text.index('    local res status');end=text.index('\n}\n',start)
  block=text[start:end].replace('"/tmp/${IF_NAME}.conf.$$"','"$SAFE_TEMP/conf"')
  script=root/name
  script.write_text("""WG=fixture_wg
IF_NAME=synthetic
fixture_wg(){ if test "$1" = setconf; then printf '%s' "$MESSAGE"; return "$RESULT"; fi; return 0; }
log(){ :; }
send_ping(){ :; }
run_result(){
"""+block+'\n}\nrun_result "$MODE"\n')
  for result,message in [('0',''),('0','diagnostic error word'),('5','permission denied'),('7','')]:
   for mode in ['', 'reconnect'] if name=='wgc.sh' else ['']:
    r=subprocess.run(['sh',str(script)],env=dict(os.environ,RESULT=result,MESSAGE=message,MODE=mode,SAFE_TEMP=str(root)),capture_output=True,text=True,timeout=10)
    assert (r.returncode==0)==(result=='0'),(name,result,message,mode,r.stderr)
print('PASS synthetic setconf status: both controllers, non-error-word failure and reconnect propagation; runtime unverified')
