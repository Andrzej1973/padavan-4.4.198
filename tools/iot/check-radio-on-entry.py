"""Saved radio ON admission: native versus owned versus refused is explicit."""
from pathlib import Path
import ast,subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-restart-entry.py').read_text()
body=next(ast.literal_eval(n.value) for n in ast.parse(source).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='code' for t in n.targets))
body=body.split('int main(void){',1)[0]
body=body.replace('int wr_iot_rc_radio_off_receipt(struct wr_iot_physical_stop_request*r){(void)r;assert(0);return 0;}', 'static int has_receipt=1,receipt_reads,receipt_drift;\nint wr_iot_rc_radio_off_receipt(struct wr_iot_physical_stop_request*r){receipt_reads++;if(!has_receipt)return 0;*r=(struct wr_iot_physical_stop_request){WR_STOP_RELEASE,1,2,3,4,5,{1}};if(receipt_drift&&receipt_reads==2)r->attempt++;return 1;}')
body=body.replace('int wr_iot_rc_radio_on_saved_request(struct wr_iot_request*r){(void)r;assert(0);return 0;}', 'static int saved_ok=1;\nint wr_iot_rc_radio_on_saved_request(struct wr_iot_request*r){assert(held);memset(r,0,sizeof(*r));return saved_ok;}')
body=body.replace('int wr_iot_rc_radio_on_begin(const struct wr_iot_control_request*r,int reload){(void)r;(void)reload;assert(0);return 0;}', 'static int on_calls;\nint wr_iot_rc_radio_on_begin(const struct wr_iot_control_request*r,int reload){assert(!held&&!r->request.enabled&&r->created&&strlen(r->id)==32&&reload==1);on_calls++;return claimed;}')
body+=r'''
int main(void){
 assert(wr_iot_radio_on_entry(0,1)==WR_RADIO_ENTRY_NATIVE&&!on_calls);
 has_receipt=0;assert(wr_iot_radio_on_entry(1,1)==WR_RADIO_ENTRY_NATIVE&&!held&&!on_calls);has_receipt=1;
 wr_iot_rc_shutdown.radio_on_owned=1;assert(wr_iot_radio_on_entry(1,1)==WR_RADIO_ENTRY_REFUSED&&!on_calls);wr_iot_rc_shutdown.radio_on_owned=0;
 saved_ok=0;assert(wr_iot_radio_on_entry(1,1)==WR_RADIO_ENTRY_REFUSED&&!held&&!on_calls);saved_ok=1;
 entropy_ok=0;assert(wr_iot_radio_on_entry(1,1)==WR_RADIO_ENTRY_REFUSED&&!held&&!on_calls);entropy_ok=1;
 receipt_reads=0;receipt_drift=1;assert(wr_iot_radio_on_entry(1,1)==WR_RADIO_ENTRY_REFUSED&&!held&&!on_calls);receipt_drift=0;
 assert(wr_iot_radio_on_entry(1,1)==WR_RADIO_ENTRY_OWNED&&on_calls==1&&!held);
 claimed=0;assert(wr_iot_radio_on_entry(1,1)==WR_RADIO_ENTRY_REFUSED&&on_calls==2&&!held);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-radio-on-entry-') as d:
 p=Path(d)/'check.c';p.write_text(body);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=5)
print('PASS saved ON entry: missing receipt selects native, owned/refused distinct, guard released before root, mode/snapshot/entropy/receipt-drift failures never fall through; SDK/root actors')
