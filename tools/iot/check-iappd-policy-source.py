"""Candidate installer refuses incomplete inputs before mutation."""
from pathlib import Path
import subprocess,tempfile,json
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='wr-iapp-policy-source-') as d:
 root=Path(d);fw=root/'trunk/user/rc/firewall_ex.c';sh=root/'trunk/user/ralinkiappd/iappd.sh'
 fw.parent.mkdir(parents=True);sh.parent.mkdir(parents=True)
 text=''
 for name,ret in [('ipt_filter_rules','return 0;'),('ipt_filter_default','return;')]:
  text+='\n'+name+'(FILE*fp)\n{\n#if defined(BOARD_WR1200JS)\n if(!wr_iot_firewall_quarantine(fp)){fclose(fp);logmessage("IoT Wi-Fi","Firewall quarantine write failed");'+ret+'}\n#endif\n}\n'
 (fw.parent/'wr-iot').mkdir();(fw.parent/'wr-iot/restart-iapp-policy.h').write_text('#define WR_IOT_IAPP_POLICY_PREPARED 0\n')
 fw.write_text(text);sh.write_text('#!/bin/sh\nstart(){\n'+''.join('iptables -A INPUT -i br0 -p '+p+' --dport 3517 -j ACCEPT\n' for p in ('tcp','udp'))+'}\n');sh.chmod(0o755)
 cmd=['python3','-B',str(here/'prepare-iappd-policy-source.py'),str(root)]
 before=(fw.read_bytes(),sh.read_bytes())
 for board,ready in [('other',False),('WR1200JS',True)]:
  (root/'iot-runtime-source.json').write_text(json.dumps({'board':board,'production_ready':ready}))
  assert subprocess.run(cmd,capture_output=True).returncode and before==(fw.read_bytes(),sh.read_bytes())
 (root/'iot-runtime-source.json').write_text(json.dumps({'board':'WR1200JS','production_ready':False}))
 gate=fw.parent/'wr-iot/restart-iapp-policy.h'
 gate.write_text('#define WR_IOT_IAPP_POLICY_PREPARED 1\n')
 assert subprocess.run(cmd,capture_output=True).returncode and before==(fw.read_bytes(),sh.read_bytes())
 gate.write_text('#define WR_IOT_IAPP_POLICY_PREPARED 0\n')
 subprocess.run(cmd,check=True)
 report=json.loads((root/'iot-iapp-policy-source.json').read_text());assert report['iapp_root_launch_bound']
 assert fw.read_text().count('WR_IAPP_BUILDER_RULES')==2 and 'iptables -A' not in sh.read_text()
 assert sh.stat().st_mode&0o777==0o755
 subprocess.run(['python3','-B',str(here/'check-iappd-policy-manifest.py'),str(root)],check=True)
 original=sh.read_text();sh.write_text(original+'# drift\n')
 assert subprocess.run(['python3','-B',str(here/'check-iappd-policy-manifest.py'),str(root)],capture_output=True).returncode
 sh.write_text(original)
 after=(fw.read_bytes(),sh.read_bytes());assert subprocess.run(cmd,capture_output=True).returncode and after==(fw.read_bytes(),sh.read_bytes())
print('PASS candidate policy installer: board/experimental/duplicate refusal before mutation, paired output/manifest and executable mode preserved; SDK bodies separately checked, no target claim')
