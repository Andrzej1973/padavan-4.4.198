from pathlib import Path
import ast,subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-restart-main-controller.py').read_text()
code=next(ast.literal_eval(n.value) for n in ast.parse(source).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='code' for t in n.targets))
code=code.replace('enum wr_iot_main_bridge_result wr_iot_restart_main_bridge_attach(void){assert(0);return WR_MAIN_BRIDGE_REFUSED;}','static int attaches,membership;\nenum wr_iot_main_bridge_result wr_iot_restart_main_bridge_attach(void){attaches++;return WR_MAIN_BRIDGE_UNCERTAIN;}').replace('int wr_iot_restart_main_bridge_current(void){assert(0);return 0;}','int wr_iot_restart_main_bridge_current(void){return membership;}')
a=code.index('int main(void)');code=code[:a]+r'''
int main(void){
 struct wr_iot_restart_generation g={.owner=getpid(),.phase=WR_RESTART_GEN_VERIFIED,.profile={.active=1},.origin={.physical={.epoch=1,.generation=3}}};
 struct wr_iot_restart_main s={0};unsigned char id[16]={7};wr_iot_rc_shutdown.active=1;outcome=WR_RESTART_UP_RETURNED;
 assert(wr_iot_restart_main_begin(&s,&g,id));
 probe_ok=0;assert(!wr_iot_restart_main_lan_step(&s)&&!attaches&&!s.bridge_attempted);probe_ok=1;
 assert(!wr_iot_restart_main_lan_step(&s)&&attaches==1&&s.bridge_attempted);
 for(unsigned i=0;i<3;i++)assert(!wr_iot_restart_main_lan_step(&s)&&attaches==1);
 membership=1;assert(wr_iot_restart_main_lan_step(&s)&&attaches==1&&calls==1&&g.profile.active);
 epoch=3;assert(!wr_iot_restart_main_lan_step(&s)&&attaches==1);epoch=2;
 wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_restart_main_lan_step(&s)&&attaches==1);wr_iot_rc_shutdown.pending=0;
 assert(wr_iot_restart_main_lan_step(&s)&&attaches==1);
 puts("PASS Main READY LAN step: add attempted once, uncertain membership readback only, no mutation before driver readiness, epoch/pending refusal, baseline held; bridge/driver actors injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-main-lan-') as d:
 p=Path(d)/'check.c';p.write_text(code);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True)
