from pathlib import Path
root=Path(__file__).resolve().parent
text=(root/'check-physical-scheduler-wan-iapp.py').read_text()
extra=r'''
backend=backend.replace('static int fail_unmask;', 'static int fail_unmask,boundary_arm,boundary_done,boundary_retained;')
a=' return sigprocmask(how,set,old);'
assert a in backend
backend=backend.replace(a,' if(how==SIG_SETMASK&&boundary_arm){boundary_arm=0;boundary_done=1;expected_iapp_shutdown=1;assert(!raise(SIGTERM));}\n'+a,1)
a='  if(!finish&&pump.phase==WR_RESUME_REBIND){'
assert a in backend
backend=backend.replace(a,r"""
  if(finish&&!strcmp(mode,"finish_boundary")&&pump.phase==WR_RESUME_FINISH&&!boundary_done)boundary_arm=1;
  if(finish&&!strcmp(mode,"finish_iapp_boundary")&&pump.phase==WR_RESUME_WAN&&pump.terminal.attempted&&!boundary_done)boundary_arm=1;
  if(boundary_done&&!boundary_retained){
   assert(!physical_replays&&backend.phase==WR_IOT_OWNER_ACTIVE);
   if(!strcmp(mode,"finish_boundary")){
    struct wr_iot_rc_physical_resume held={0};assert(wr_iot_rc_physical_resume_read(&held));
    assert(pump.phase==WR_RESUME_FINISH&&initial_restart_retained()&&pump.restore.generation.origin.desired.password[0]);
   }else assert(pump.phase==WR_RESUME_WAN&&pump.terminal.child&&pump.terminal.guard==1);
   boundary_retained=1;close_result=progress_result=release_result=WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;
  }
"""+a,1)
backend=backend.replace('if(finish&&!strcmp(mode,"finish_pending")){', 'if(finish&&(!strcmp(mode,"finish_pending")||strstr(mode,"boundary"))){')
backend=backend.replace('assert(late_signal&&late_unmask&&pump.phase==WR_RESUME_CANCELLED&&!physical_replays&&wr_iot_rc_shutdown.normal_route_armed&&wr_iot_rc_shutdown.normal_route_requested==SIGTERM);',
 'assert((strstr(mode,"boundary")?(boundary_done&&boundary_retained):(late_signal&&late_unmask))&&pump.phase==WR_RESUME_CANCELLED&&(!strcmp(mode,"finish_boundary")?(!wr_iot_rc_shutdown.normal_route_armed&&physical_replays==1):(wr_iot_rc_shutdown.normal_route_armed&&wr_iot_rc_shutdown.normal_route_requested==SIGTERM&&!physical_replays)));')
a='  assert(wan_plans==1&&wan_dispatches==1&&wan_leds==1);\n  assert(wr_iot_restart_scheduler_step()==-1);physical_fixture_terminal();\n  int st;assert(waitpid(-1,&st,0)>0&&WIFEXITED(st)&&WEXITSTATUS(st)==0);'
assert a in backend
backend=backend.replace(a,r"""
  assert(wan_plans==1);
  if(!strcmp(mode,"finish_boundary"))assert(!wan_dispatches&&!wan_leds&&!pump.restore.iapp.attempted);
  else{assert(wan_dispatches==1&&wan_leds==1);int st;assert(waitpid(-1,&st,0)>0&&WIFEXITED(st)&&WEXITSTATUS(st)==0);}
  assert(wr_iot_restart_scheduler_step()==-1);physical_fixture_terminal();
""")
'''
needle="text=text.replace(marker,'extra+='+repr(extra)+'\\n'+marker,1)"
assert needle in text
text=text.replace(needle,'extra+='+repr(extra)+'\n'+needle,1)
# Final generated harness adds both boundary processes; only IAPP boundary runs a script.
needle="exec(compile(text,__file__,'exec'),{'__file__':__file__})"
patch=r'''
a=" assert (p/'iapp-events').read_text().splitlines()==['restart','restart']\\n"
assert a in text
text=text.replace(a," subprocess.run([d+'/check',d],check=True,timeout=30,env={**os.environ,'WR_PHYSICAL_RESUME_TEST':'finish_boundary'})\\n subprocess.run([d+'/check',d],check=True,timeout=30,env={**os.environ,'WR_PHYSICAL_RESUME_TEST':'finish_iapp_boundary'})\\n assert (p/'iapp-events').read_text().splitlines()==['restart','restart','restart']\\n",1)
'''
i=text.rfind(needle);assert i>=0
text=text[:i]+patch+'\n'+text[i:]
exec(compile(text,__file__,'exec'),{'__file__':__file__})
