"""Actual INITIAL physical claim; selected-lifetime observer injected."""
from pathlib import Path
root=Path(__file__).resolve().parent
source=(root/'check-initial-saved-physical.py').read_text()
marker="with tempfile.TemporaryDirectory(prefix='wr-initial-desired-') as d:"
extra=r'''
code=code.replace('int wr_iot_initial_restart_selected_current(const unsigned char*n,const struct wr_iot_idle_result*r){(void)n;(void)r;assert(0);return 0;}', '')
code=code.replace('static int saved_ok=1,saved_enabled=1,saved_reads;', 'static int selected_ok,selected_reads;\nint wr_iot_initial_restart_selected_current(const unsigned char*n,const struct wr_iot_idle_result*r){assert(depth==1&&wr_iot_rc_shutdown.active&&!downs&&!initial_calls&&n[0]==7&&r->epoch==11&&r->generation==12&&r->serial==9);selected_reads++;return selected_ok;}\nstatic int saved_ok=1,saved_enabled=1,saved_reads;')
code=code.replace('saved_ok=argc!=2;saved_enabled=argc!=3;', 'saved_ok=1;saved_enabled=1;selected_ok=argc!=2;unsigned char nonce[16]={7};struct wr_iot_idle_result selected={11,12,9};')
code=code.replace('wr_iot_rc_physical_begin_initial_saved(&intent)', 'wr_iot_rc_physical_begin_initial_selected(&intent,nonce,&selected)')
code=code.replace('if(!saved_ok){', 'assert(selected_reads==1);if(!selected_ok){')
code=code.replace('assert(physical.finishing==-1&&!physical.initial_saved);', 'assert(physical.finishing==-1&&physical.initial_saved);')
'''
assert source.count(marker)==1
source=source.replace(marker,extra+'\n'+marker,1)
exec(compile(source,__file__,'exec'),{'__file__':__file__})
print('PASS selected INITIAL physical claim: checked under actual guard/admission before ARM/DOWN; mismatch retains claim then cleans credentials without hardware calls; lifetime observer actor')
