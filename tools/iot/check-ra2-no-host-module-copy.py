"""Exercise the actual CI source-install block without copying/building a kernel."""
import hashlib,json,subprocess,sys,tempfile
from pathlib import Path
here=Path(__file__).resolve().parent
shell=(here/'ci-compile-ra2-no-host-module.sh').read_text()
block=shell.split("<<'PY'\n",1)[1].split('\nPY\n',1)[0]
with tempfile.TemporaryDirectory(prefix='wr-no-host-copy-') as tmp:
 root=Path(tmp);source=root/'source';driver=root/'driver';results=root/'results'
 source.mkdir();driver.mkdir();results.mkdir()
 files={'include/rtmp.h':'#include "physical-stop-record.h"\n',
        'include/physical-stop-record.h':'/* later composed layer */\n',
        'os/linux/rt_main_dev.c':'/* later Main hook */\n'}
 for name,text in files.items():
  path=source/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
 manifest={'production_installed':False,'ra2_no_host_experiment':{
  'activation_ready':False,'changed_paths':['include/rtmp.h']},
  'candidate_driver_sha256':{n:hashlib.sha256((source/n).read_bytes()).hexdigest() for n in files}}
 Path(str(source)+'.manifest.json').write_text(json.dumps(manifest))
 def run():return subprocess.run([sys.executable,'-B','-c',block,str(source),str(driver),str(results)],capture_output=True,text=True)
 result=run();assert result.returncode==0,result.stderr
 for name in files:assert (driver/name).read_bytes()==(source/name).read_bytes(),name
 (source/'include/physical-stop-record.h').write_text('drift')
 result=run();assert result.returncode!=0 and 'Experiment input drift' in result.stderr
 assert (driver/'include/physical-stop-record.h').read_text()==files['include/physical-stop-record.h']
print('PASS actual CI install block: later physical-stop header/Main hook copied; drift refused before copying')
