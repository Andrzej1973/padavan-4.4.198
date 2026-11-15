/* Candidate composition after rc-backend's private backend/rebind objects.
 * Requires cold-on-owner and activation-observe declarations. No standalone
 * globals exported; public routing remains a separate step. */
static const struct wr_iot_cold_owner *wr_iot_cold_backend_parent;
static struct wr_iot_driver_identity wr_iot_cold_backend_identity;
static int wr_iot_cold_request_same(const struct wr_iot_control_request *a,
 const struct wr_iot_control_request *b)
{
 if(!a||!b||!a->created||a->created!=b->created||a->request.enabled!=1||b->request.enabled!=1||
    !memchr(a->id,0,sizeof(a->id))||!memchr(b->id,0,sizeof(b->id))||
    !wr_iot_control_id(a->id)||strcmp(a->id,b->id))return 0;
#define COLD_SAME(f) if(!memchr(a->request.f,0,sizeof(a->request.f))||!memchr(b->request.f,0,sizeof(b->request.f))||strcmp(a->request.f,b->request.f))return 0;
 COLD_SAME(ssid) COLD_SAME(password) COLD_SAME(gateway) COLD_SAME(mask) COLD_SAME(first) COLD_SAME(last)
#undef COLD_SAME
 return 1;
}
int wr_iot_rc_cold_start_begin(struct wr_iot_cold_owner *parent,
 const struct wr_iot_control_request *request)
{
 struct wr_iot_control_request expected={0};int guard,claimed=0;
 if(!parent||!request||parent->owner!=getpid()||parent->busy||parent->phase!=WR_COLD_OWNER_PREPARED||
    wr_iot_cold_backend_parent||rebind.owner||backend.busy||backend.start.owner||backend.stop.owner||
    backend.start.admission.snapshot.active||backend.start.admission.snapshot.token||
    !((!backend.owner&&backend.phase==WR_IOT_OWNER_IDLE)||
      (backend.owner==getpid()&&backend.phase==WR_IOT_OWNER_INITIAL_OFF))||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||!wr_iot_rc_shutdown.radio_off_owned||
    wr_iot_rc_shutdown.radio_on_owned)return 0;
 expected=parent->input;expected.request=parent->generation.desired;
 if(!wr_iot_cold_request_same(request,&expected))goto done;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)goto done;
 if(backend.phase==WR_IOT_OWNER_INITIAL_OFF&&
    (backend.initial_off.owner!=getpid()||!backend.initial_off.ready||!backend.initial_off.created||
     !memchr(backend.initial_off.id,0,sizeof(backend.initial_off.id))||!wr_iot_control_id(backend.initial_off.id)||
     !strcmp(request->id,backend.initial_off.id)||request->created<backend.initial_off.created))goto release;
 if(!wr_iot_cold_owner_step(parent)||!parent->main.identity.adapter_epoch||
    !parent->main.identity.device_generation||wr_iot_rc_shutdown.pending)goto release;
 /* Existing initial admission performs its own two fresh IDLE observations
  * and captures RAM rollback under a nested guard; no fabricated RELEASE. */
 (void)wr_iot_start_runner_begin(&backend.start,request,1,1,0);
 if(!backend.start.owner)goto release;
 wr_iot_cold_backend_parent=parent;wr_iot_cold_backend_identity=parent->main.identity;
 backend.owner=getpid();backend.phase=backend.start.phase==WR_IOT_RUN_REJECTED?
  WR_IOT_OWNER_REJECTED:WR_IOT_OWNER_START;claimed=1;
 if(backend.start.admission.admitted&&
    (backend.start.admission.idle.epoch!=wr_iot_cold_backend_identity.adapter_epoch||
     backend.start.admission.idle.generation!=wr_iot_cold_backend_identity.device_generation)){
  backend.start.phase=WR_IOT_RUN_UNCERTAIN;backend.phase=WR_IOT_OWNER_START;
 }
 release:wr_iot_service_guard_leave(guard);
 done:{volatile unsigned char*p=(volatile unsigned char*)&expected;size_t n=sizeof(expected);while(n--)*p++=0;}
 return claimed;
}
int wr_iot_rc_cold_active_current(const struct wr_iot_cold_owner *parent,
 const struct wr_iot_control_request *request)
{
 struct wr_iot_control_result observed={0};int guard,ok=0;
 if(!parent||!request||wr_iot_cold_backend_parent!=parent||parent->owner!=getpid()||parent->busy||
    parent->phase!=WR_COLD_OWNER_PREPARED||parent->admission.owner!=getpid()||
    parent->admission.guard!=1||parent->admission.busy!=1||
    parent->admission.fence.owner!=getpid()||parent->admission.fence.level!=1||
    parent->generation.owner!=getpid()||parent->generation.busy||
    !parent->generation.main_may_have_started||parent->generation.admission!=&parent->admission||
    parent->main.generation!=&parent->generation||rebind.owner||backend.owner!=getpid()||backend.busy||backend.phase!=WR_IOT_OWNER_ACTIVE||
    backend.start.owner!=getpid()||backend.start.busy||backend.start.phase!=WR_IOT_RUN_ACTIVE||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||!wr_iot_rc_shutdown.radio_off_owned||wr_iot_rc_shutdown.radio_on_owned||
    parent->main.identity.adapter_epoch!=wr_iot_cold_backend_identity.adapter_epoch||
    parent->main.identity.device_generation!=wr_iot_cold_backend_identity.device_generation||
    backend.start.open.attempt.identity.adapter_epoch!=wr_iot_cold_backend_identity.adapter_epoch||
    backend.start.open.attempt.identity.device_generation!=wr_iot_cold_backend_identity.device_generation||
    !wr_iot_cold_request_same(request,&backend.start.input))return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 memcpy(observed.id,request->id,sizeof(observed.id));observed.created=request->created;
 observed.state=WR_IOT_RESULT_APPLIED;
 ok=wr_iot_activation_owner_observed(&backend,&observed)&&!wr_iot_rc_shutdown.pending;
 wr_iot_service_guard_leave(guard);return ok;
}

int wr_iot_rc_cold_start_progress(const struct wr_iot_cold_owner *parent,
 const struct wr_iot_control_request *request)
{
 int guard;
 if(!parent||!request||wr_iot_cold_backend_parent!=parent||parent->owner!=getpid()||parent->busy||
    parent->phase!=WR_COLD_OWNER_PREPARED||parent->generation.admission!=&parent->admission||
    parent->main.generation!=&parent->generation||!parent->generation.main_may_have_started||
    parent->admission.owner!=getpid()||parent->admission.busy!=1||parent->admission.guard!=1||
    parent->admission.fence.owner!=getpid()||parent->admission.fence.level!=1||
    rebind.owner||backend.owner!=getpid()||backend.busy||backend.phase!=WR_IOT_OWNER_START||
    backend.start.owner!=getpid()||backend.start.busy||!backend.start.admission.admitted||
    backend.start.admission.idle.epoch!=wr_iot_cold_backend_identity.adapter_epoch||
    backend.start.admission.idle.generation!=wr_iot_cold_backend_identity.device_generation||
    parent->main.identity.adapter_epoch!=wr_iot_cold_backend_identity.adapter_epoch||
    parent->main.identity.device_generation!=wr_iot_cold_backend_identity.device_generation||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||!wr_iot_rc_shutdown.radio_off_owned||wr_iot_rc_shutdown.radio_on_owned||
    !wr_iot_cold_request_same(request,&backend.start.input))return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 (void)wr_iot_activation_owner_continue(&backend,request->id,request->created);
 wr_iot_service_guard_leave(guard);return 1;
}
