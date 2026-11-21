"""Native cold admission must respect separate ON/OFF process ownership."""
from pathlib import Path
import subprocess,sys,tempfile
here=Path(__file__).resolve().parent
ns={'__file__':str(here/'check-rc-backend-composition.py')}
source=(here/'check-rc-backend-composition.py').read_text()
# Preserve the existing full composition; add the exclusion scenario where
# native initial-OFF admission is otherwise known to succeed.
a='entropy_fail=0;assert(wr_iot_activation_prepare_radio_stop()&&!depth);'
b=a+r'''
 unsigned prior_idle=idle_reads;
 wr_iot_rc_shutdown.radio_on_owned=1;
 assert(!wr_iot_activation_prepare_radio_stop()&&idle_reads==prior_idle&&!depth);
 wr_iot_rc_shutdown.radio_on_owned=0;wr_iot_rc_shutdown.radio_off_owned=1;
 assert(!wr_iot_activation_prepare_radio_stop()&&idle_reads==prior_idle&&!depth);
 wr_iot_rc_shutdown.radio_off_owned=0;
 assert(wr_iot_activation_prepare_radio_stop()&&idle_reads==prior_idle+2&&!depth);
'''
assert source.count(a)==1
source=source.replace(a,b)
if len(sys.argv)==2:
 source=source.replace('#include "rc-backend.c"','#include "'+str(Path(sys.argv[1]).resolve())+'"')
exec(compile(source,str(here/'check-rc-backend-composition.py'),'exec'),ns)
print('PASS native process exclusion: ON/OFF ownership refuses before idle/guard activity, release restores ordinary initial-OFF admission; actual backend fixture')
