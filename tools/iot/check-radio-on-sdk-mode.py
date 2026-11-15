"""Full restore fixture with actual rc-mode adapter, live OFF and saved ON."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-radio-on-restore.py').read_text()
ns={'__file__':str(here/'check-radio-on-restore.py')}
exec(source.rsplit('with tempfile.TemporaryDirectory(',1)[0],ns)
body=ns['body']
anchor='int wr_iot_rc_radio_on_mode_read(struct wr_iot_rc_mode *m){m->router=m->radio=1;m->mode=0;return 1;}'
assert body.count(anchor)==1
body=body.replace(anchor,r'''
static int saved_radio=1;
int get_ap_mode(void){return 0;}
int get_enabled_radio_rt(void){return saved_radio;}
int get_mode_radio_rt(void){return 0;}
int is_radio_on_rt(void){return !down;}
#include "rc-mode.c"
''')
anchor='int main(int argc,char**argv){'
assert body.count(anchor)==1
body=body.replace(anchor,anchor+r'''
 struct wr_iot_rc_mode live={0},saved={0};
 depth=1;down=1;
 assert(wr_iot_rc_mode_read(&live)&&!live.radio);
 assert(wr_iot_rc_radio_on_mode_read(&saved)&&saved.radio==1);
 depth=0;saved_radio=0;
 struct wr_iot_on_admission refused={0};assert(!wr_iot_on_admission_begin(&refused)&&!refused.owner&&!depth&&!wr_iot_rc_shutdown.active);
 saved_radio=1;
''')
with tempfile.TemporaryDirectory(prefix='wr-on-sdk-mode-') as d:
    root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n')
    p=root/'check.c';p.write_text(body);b=root/'check'
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
    subprocess.run([str(b),d],check=True,timeout=15)
print('PASS actual RC mode + ON restore composition: live OFF remains radio0 while saved ON admits full profile/RAM/Main/Guest/MC/services; saved OFF refuses before fence; original live-reader semantics unchanged; SDK queries/transports injected')
