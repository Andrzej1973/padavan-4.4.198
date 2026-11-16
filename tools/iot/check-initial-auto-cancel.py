from pathlib import Path
here=Path(__file__).resolve().parent
source=(here/'check-physical-parent-backend-composed.py').read_text()
cut=source.index('\nwith tempfile.TemporaryDirectory(')
ns={'__file__':str(here/'check-physical-parent-backend-composed.py')}
exec(compile(source[:cut],'<actual initial setup>','exec'),ns)
physical=ns['physical']
backend=ns['backend']
for name in ['wr_iot_rc_normal_shutdown_arm_ready','wr_iot_rc_normal_shutdown_arm_commit']:backend=ns['remove_function'](backend,name)
a='static volatile sig_atomic_t physical_replays;';assert a in backend
backend=backend.replace(a,'#include "rc-normal-shutdown.c"\n'+a,1)
a='assert(!backend.start.input.request.password[0]&&physical_replays==1);';assert a in backend
backend=backend.replace(a,a+'assert(!wr_iot_rc_shutdown.normal_route_armed);',1)
a='physical_fixture_terminal();assert(wr_iot_rc_initial_restart_postrelease_current(&receipt));';assert a in backend
backend=backend.replace(a,a+'assert(wr_iot_rc_shutdown.normal_route_armed);',1)
tail=source[cut:]
a=" physical_public={'wr_iot_physical_stop_call'";assert a in tail
tail=tail.replace(a," physical_public={'wr_iot_rc_physical_begin_routed_shutdown','wr_iot_rc_physical_pending','wr_iot_rc_physical_step','wr_iot_rc_physical_off_failed','wr_iot_rc_physical_shutdown_release_cleanup','wr_iot_physical_stop_call'",1)
ns.update(physical=physical,backend=backend,tail=tail)
exec(compile(tail,__file__,'exec'),ns)
print('PASS automatic-arm actual-source cancellation: ACTIVE finish armed; stage/network/commit/committed/uncertain cancellation and disabled INITIAL leave route unarmed; actual parent/backend/physical with resource actors')
