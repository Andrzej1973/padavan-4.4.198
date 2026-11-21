"""Actual INITIAL cleanup auto-arms real normal shutdown, including cleanup-time TERM."""
from pathlib import Path
here=Path(__file__).resolve().parent
source=(here/'check-initial-postrelease-normal-shutdown.py').read_text()
cut=source.rindex('exec(compile(tail,')
ns={'__file__':str(here/'check-initial-postrelease-normal-shutdown.py')}
exec(compile(source[:cut],'<postrelease composition>','exec'),ns)
backend=ns['backend']
a='expected_normal_off=1;assert(wr_iot_rc_shutdown_route_arm()&&!raise(SIGTERM)&&!physical_replays);'
assert a in backend
backend=backend.replace(a,r'''expected_normal_off=1;
 assert(wr_iot_rc_shutdown.normal_route_armed);
 if(getenv("WR_ARM_COMMIT_SIGNAL"))assert(wr_iot_rc_shutdown.normal_route_requested==SIGTERM);
 else assert(!wr_iot_rc_shutdown.normal_route_requested);
 assert(!raise(SIGTERM)&&!physical_replays);''',1)
a=' struct wr_iot_activation_owner retained_active=backend;fail_unmask=1;'
assert a in backend
backend=backend.replace(a,r''' struct wr_iot_activation_owner before_refusal=backend;
 normal_shutdown.spent=1;
 assert(!wr_iot_rc_physical_resume_finish(&parent)&&initial_restart_retained());
 assert(parent.phase==WR_RESTORE_HANDOFF&&!parent.busy&&parent.generation.origin.desired.password[0]);
 assert(wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.normal_route_armed);
 assert(!memcmp(&before_refusal,&backend,sizeof(backend))&&depth==1);
 normal_shutdown.spent=0;
'''+a,1)
tail=ns['tail']
a=" (p/'rc.h').write_text";assert a in tail
tail=tail.replace(a,r''' injected=p/'rc-initial-restart-detach.inc'
 text=(here/'rc-initial-restart-detach.inc').read_text()
 anchor='if(backend.phase==WR_IOT_OWNER_ACTIVE)wr_iot_rc_normal_shutdown_arm_commit();'
 assert anchor in text
 injected.write_text(text.replace(anchor,'if(backend.phase==WR_IOT_OWNER_ACTIVE){if(getenv("WR_ARM_COMMIT_SIGNAL"))assert(!raise(SIGTERM));wr_iot_rc_normal_shutdown_arm_commit();}',1))
'''+a,1)
a=" subprocess.run([d+'/check',d],check=True,timeout=30)";assert a in tail
tail=tail.replace(a,a+"\n import os\n subprocess.run([d+'/check',d],check=True,timeout=30,env={**os.environ,'WR_ARM_COMMIT_SIGNAL':'1'})",1)
ns.update(backend=backend,tail=tail)
exec(compile(tail,__file__,'exec'),ns)
print('PASS automatic INITIAL shutdown: actual parent/backend/physical cleanup auto-arms real normal consumer; TERM inside cleanup retained through OFF/physical RELEASE before one stock replay; hardware/network actors, no device proof')
