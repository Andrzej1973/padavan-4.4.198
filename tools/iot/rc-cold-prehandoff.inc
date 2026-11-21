/* RC-private predicate after cold backend declarations. Pending normal shutdown
 * may observe an idle backend, never an existing claimed initial-start owner. */
int wr_iot_rc_cold_never_started(const struct wr_iot_cold_owner *parent)
{
 return parent&&parent->owner==getpid()&&!parent->busy&&
  !wr_iot_cold_backend_parent&&!rebind.owner&&!backend.busy&&!backend.start.owner&&!backend.stop.owner&&
  !backend.start.admission.snapshot.active&&!backend.start.admission.snapshot.token&&
  ((!backend.owner&&backend.phase==WR_IOT_OWNER_IDLE)||
   (backend.owner==getpid()&&backend.phase==WR_IOT_OWNER_INITIAL_OFF));
}
