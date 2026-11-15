"""Actual saved mode/NVRAM adapter; borrowed buffer and snapshot drift."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-radio-on-sdk-mode.py')}
exec((here/'check-radio-on-sdk-mode.py').read_text().rsplit('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body'].split('int main(int argc',1)[0]
a='const char *v=!strcmp(key,"wr_iot_enable")?saved_enabled:!strcmp(key,"wr_iot_ssid")?saved_ssid:saved_password;'
b='const char *v=!strcmp(key,"wr_iot_gateway")?"192.168.50.1":!strcmp(key,"wr_iot_mask")?"255.255.255.0":!strcmp(key,"wr_iot_start")?"192.168.50.20":!strcmp(key,"wr_iot_end")?"192.168.50.200":!strcmp(key,"wr_iot_enable")?saved_enabled:!strcmp(key,"wr_iot_ssid")?saved_ssid:saved_password;'
assert body.count(a)==1
body=body.replace(a,b)+r'''
int main(void){
 (void)check;struct wr_iot_request r={.enabled=7};
 guard=0;assert(!wr_iot_rc_radio_on_saved_request(&r)&&r.enabled==7);guard=1;
 reads=0;strcpy(saved_enabled,"1");assert(wr_iot_rc_radio_on_saved_request(&r)&&r.enabled==1&&!strcmp(r.ssid,"IoT")&&!strcmp(r.gateway,"192.168.50.1"));
 struct wr_iot_request retained=r;reads=0;drift=1;assert(!wr_iot_rc_radio_on_saved_request(&r)&&!memcmp(&r,&retained,sizeof(r)));drift=0;strcpy(saved_ssid,"IoT");
 strcpy(saved_enabled,"0");assert(wr_iot_rc_radio_on_saved_request(&r)&&!r.enabled&&!r.ssid[0]&&!r.password[0]);
 saved_radio=0;assert(!wr_iot_rc_radio_on_saved_request(&r));
}
'''
with tempfile.TemporaryDirectory(prefix='wr-on-saved-request-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
 p=root/'check.c';p.write_text(body);b=root/'check'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS actual saved request: shared borrowed buffer copied, valid ON subnet/credentials, OFF carries no secrets, drift/guard/saved-radio refusal preserves output; no writes')
