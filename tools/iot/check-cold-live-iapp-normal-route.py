"""Armed cold normal-shutdown route drains an already owned IAPP child."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-rc-cold-final-shutdown.py').read_text();ns={'__file__':str(here/'check-rc-cold-final-shutdown.py')}
exec(compile(source[:source.index('\nwith tempfile.TemporaryDirectory(')],'<actual cold final fixture>','exec'),ns)
body=ns['body']
a=' wr_iot_rc_shutdown.radio_on_owned=1;';assert body.count(a)==1
body=body.replace(a,a+'\n if(enabled)assert(wr_iot_rc_shutdown_route_arm());',1)
a='&&!depth&&signals==old_signals+1);';assert body.count(a)==1
body=body.replace(a,'&&!depth&&signals==old_signals+(enabled?0:1));',1)
a='  assert(off_calls==old_off+enabled&&launches==old_launches);';assert a in body
body=body.replace(a,a+r'''
  if(enabled){
   assert(wr_iot_rc_shutdown.normal_route_armed&&wr_iot_rc_shutdown.normal_route_requested==SIGTERM);
   assert(!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending&&!wr_iot_rc_shutdown.radio_on_owned);
   assert(backend.phase==WR_IOT_OWNER_OFF&&!s.owner&&!wr_iot_rc_shutdown_begin());
   assert(!raise(SIGTERM)&&signals==old_signals);
   /* Fixture resets completed isolated case; production route is not cleared. */
   wr_iot_rc_shutdown.normal_route_armed=0;wr_iot_rc_shutdown.normal_route_requested=0;
  }
''',1)
with tempfile.TemporaryDirectory(prefix='wr-cold-live-route-') as d:
 p=Path(d)/'check.c';p.write_text(body)
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'restart-terminal-iapp.c'),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True,timeout=20)
print('PASS actual cold final shutdown/terminal/fence with armed route: live child retains root until drain, one OFF, failed unmask retains, cleanup routes first TERM without stock replay or new admission; enabled/disabled separation; backend/child observations actors, physical drain separately tested')
