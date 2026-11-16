from pathlib import Path
root=Path(__file__).resolve().parent
text=(root/'check-physical-wan-iapp-composed.py').read_text()
extra=r'''
a='#include "restart-resume.c"'
assert a in backend
backend=backend.replace(a,a+'\n#include "restart-scheduler.c"\n#define pump resume',1)
backend=backend.replace('struct wr_iot_restart_resume pump={0};unsigned char id[16]={7};', 'unsigned char id[16]={7};')
backend=backend.replace('wr_iot_restart_resume_begin(&pump,id,19)', 'wr_iot_restart_scheduler_begin(id,19)')
backend=backend.replace('wr_iot_restart_resume_step(&pump)', 'wr_iot_restart_scheduler_step()')
backend=backend.replace('wr_iot_restart_resume_shutdown(&pump,&off)', 'wr_iot_restart_scheduler_shutdown(off.id,off.created)')
backend=backend.replace('wr_iot_restart_resume_retire(&pump)', 'wr_iot_restart_scheduler_retire()')
backend=backend.replace('expected_iapp_shutdown=1;assert(!raise(SIGTERM));late_signal=1;',
 'expected_iapp_shutdown=1;close_result=progress_result=release_result=WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;fail_unmask=1;assert(!raise(SIGTERM));late_signal=1;')
# No manual shutdown admission in the late tail: actual scheduler must observe
# queued TERM and create the fresh OFF envelope in process context.
a='  if(late_signal&&wr_iot_rc_shutdown.pending&&pump.phase==WR_RESUME_WAN){'
assert a in backend
start=backend.index(a);end=backend.index('  if(pump.phase==WR_RESUME_POSTWAN_SHUTDOWN)',start)
backend=backend[:start]+backend[end:]
'''
marker='anchor="anchor=\'\\\\nwith tempfile.TemporaryDirectory(\'"'
# Insert after all existing backend WAN transforms, before base fixture compilation.
assert marker in text
text=text.replace(marker,'extra+='+repr(extra)+'\n'+marker,1)
marker="exec(compile(text,__file__,'exec'),{'__file__':__file__})"
assert marker in text
a="text=text.replace(anchor,staging+'\\n'+anchor,1)"
assert a in text
line="\nsource=source.replace(\" physical_public={\", \" physical_public={'wr_iot_rc_physical_restart_ready','wr_iot_rc_physical_preresume_cancel',\",1)\n"
text=text.replace(a,'staging+='+repr(line)+'\n'+a,1)
exec(compile(text,__file__,'exec'),{'__file__':__file__})
