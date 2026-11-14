"""Post-Main/pre-handoff proof with actual profile/Main fixture; actors explicit."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
source=(here/'check-restart-restore-profile-composition.py').read_text();ns={'__file__':str(here/'check-restart-restore-profile-composition.py')}
exec(compile(source[:source.index('\nwith tempfile.TemporaryDirectory(')],'<profile fixture>','exec'),ns)
body=ns['body'];body=body.replace('int main(int argc', 'static int guest_up;\nint wr_iot_restart_guest_admin_state(int*out){*out=guest_up;return 1;}\n#include "restart-prehandoff-check.c"\nint main(int argc',1)
a=body.index(' /* Process-only fixture cleanup.')
body=body[:a]+r'''
 wr_iot_rc_shutdown.pending=SIGTERM;s.guest.phase=WR_GUEST_DOWN_OBSERVED;
 assert(wr_iot_restart_prehandoff_cancel_check(&s));
 guest_up=1;assert(!wr_iot_restart_prehandoff_cancel_check(&s));guest_up=0;
 s.handoff_created=10;assert(!wr_iot_restart_prehandoff_cancel_check(&s));s.handoff_created=0;
 origin.physical.attempt++;assert(!wr_iot_restart_prehandoff_cancel_check(&s));origin.physical.attempt--;
 s.main.phase=WR_MAIN_NOT_SUBMITTED;assert(!wr_iot_restart_prehandoff_cancel_check(&s));s.main.phase=WR_MAIN_READY;
 s.main.identity.adapter_epoch++;assert(!wr_iot_restart_prehandoff_cancel_check(&s));s.main.identity.adapter_epoch--;
 s.generation.profile.files.pending=1;assert(!wr_iot_restart_prehandoff_cancel_check(&s));s.generation.profile.files.pending=0;
 s.guest.phase=WR_GUEST_ADMIN_UP;assert(!wr_iot_restart_prehandoff_cancel_check(&s));s.guest.phase=WR_GUEST_DOWN_OBSERVED;
 wr_iot_rc_shutdown.pending=0;assert(!wr_iot_restart_prehandoff_cancel_check(&s));wr_iot_rc_shutdown.pending=SIGTERM;
 assert(wr_iot_restart_prehandoff_cancel_check(&s)&&s.generation.profile.active&&generator_calls==1&&ups==1);
 char replacement[1100];snprintf(replacement,sizeof(replacement),"%s/foreign-profile",argv[1]);
 FILE*src=fopen(profile_path,"r"),*dst=fopen(replacement,"w");assert(src&&dst);int c;
 while((c=fgetc(src))!=EOF)assert(fputc(c,dst)!=EOF);
 assert(!fclose(src)&&!fclose(dst)&&!rename(replacement,profile_path));
 assert(!wr_iot_restart_prehandoff_cancel_check(&s)&&s.generation.profile.active&&ups==1&&generator_calls==1);

'''+body[a:]
with tempfile.TemporaryDirectory(prefix='wr-prehandoff-proof-') as d:
 root=Path(d);(root/'rc.h').write_text('const char *nvram_safe_get(const char *);\n');p=root/'test.c';p.write_text(body);b=root/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b),d],check=True)
print('PASS actual profile/generation/Main/root pre-handoff cancellation proof: closed rebind configuration and Guest DOWN, exact origin, no handoff/foreign Main; no profile rollback or fence release; driver/Guest actors injected')
