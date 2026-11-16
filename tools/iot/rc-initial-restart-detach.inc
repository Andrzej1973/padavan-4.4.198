/* RC-private, composed after INITIAL backend binding. Preflight runs while
 * root busy/admission held; commit is called only by successful outer cleanup.
 * Detach only the borrowed parent, leave ACTIVE backend and its keys intact. */
static void initial_restart_detach_commit(void)
{
 /* Terminal cancellation has no future credential consumer. ACTIVE finish
  * keeps its private request for ongoing full ACTIVE observation/normal OFF. */
 if(backend.phase==WR_IOT_OWNER_REJECTED||backend.phase==WR_IOT_OWNER_OFF){
  volatile unsigned char *p=(volatile unsigned char*)&backend.start.input.request;
  size_t n=sizeof(backend.start.input.request);while(n--)*p++=0;
 }
 wr_iot_initial_restart_parent=NULL;
 memset(&wr_iot_initial_restart_identity,0,sizeof(wr_iot_initial_restart_identity));
}

void wr_iot_rc_initial_restart_detach_commit(void)
{initial_restart_detach_commit();}
