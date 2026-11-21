"""Owned physical OFF entry chooses native/owned/refused without fallthrough."""
from pathlib import Path
import ast,subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-restart-entry.py').read_text()
body=next(ast.literal_eval(n.value) for n in ast.parse(source).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='code' for t in n.targets)).split('int main(void){',1)[0]
body=body.replace('int wr_iot_rc_radio_off_receipt(struct wr_iot_physical_stop_request*r){(void)r;assert(0);return 0;}', 'static int has_receipt;\nint wr_iot_rc_radio_off_receipt(struct wr_iot_physical_stop_request*r){memset(r,0,sizeof(*r));return has_receipt;}')
body=body.replace('int wr_iot_rc_radio_off_begin(const struct wr_iot_control_request*r,int reload){(void)r;(void)reload;assert(0);return 0;}', 'static int off_calls;\nint wr_iot_rc_radio_off_begin(const struct wr_iot_control_request*r,int reload){assert(!held&&reload==1&&r->created&&strlen(r->id)==32&&!r->request.enabled&&!r->request.password[0]);off_calls++;return claimed;}')
body=body.replace('int wr_iot_rc_mode_read(struct', 'static int radio_setting=1;\nint wr_iot_rc_mode_read(struct').replace('{1,1,drift','{1,radio_setting,drift')
body+=r'''
int main(void){
 assert(wr_iot_radio_off_entry(1,1)==WR_RADIO_ENTRY_NATIVE&&!off_calls);
 owned=0;assert(wr_iot_radio_off_entry(0,1)==WR_RADIO_ENTRY_NATIVE&&!off_calls);owned=1;
 has_receipt=1;assert(wr_iot_radio_off_entry(0,1)==WR_RADIO_ENTRY_REFUSED&&!off_calls&&!held);has_receipt=0;
 wr_iot_rc_shutdown.radio_on_owned=1;assert(wr_iot_radio_off_entry(0,1)==WR_RADIO_ENTRY_REFUSED&&!off_calls);wr_iot_rc_shutdown.radio_on_owned=0;
 entropy_ok=0;assert(wr_iot_radio_off_entry(0,1)==WR_RADIO_ENTRY_REFUSED&&!off_calls&&!held);entropy_ok=1;
 reads=0;drift=1;assert(wr_iot_radio_off_entry(0,1)==WR_RADIO_ENTRY_REFUSED&&!off_calls&&!held);drift=0;
 assert(wr_iot_radio_off_entry(0,1)==WR_RADIO_ENTRY_OWNED&&off_calls==1&&!held);
 radio_setting=0;assert(wr_iot_radio_off_entry(0,1)==WR_RADIO_ENTRY_OWNED&&off_calls==2&&!held);
 claimed=0;assert(wr_iot_radio_off_entry(0,1)==WR_RADIO_ENTRY_REFUSED&&off_calls==3&&!held);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-radio-off-entry-') as d:
 p=Path(d)/'check.c';p.write_text(body);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=5)
print('PASS owned OFF entry: initial path native, receipt preserved/no second OFF, busy/entropy/mode drift refused, saved radio0/1 accepted, guard released before OFF owner; controller actors')
