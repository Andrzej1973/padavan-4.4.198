/* Candidate only: structured observation, never a radio-runtime success claim. */
static void wr_modern_guest_reply(FILE *stream,const char *state,int may_change,
 int matches,const char *flash,const char *notification)
{
 fprintf(stream,"{\"schemaVersion\":1,\"state\":\"%s\",\"settingsMayHaveChanged\":%s,\"ramConfigurationMatches\":%s,\"flashCommit\":\"%s\",\"serviceNotification\":\"%s\",\"runtimeVerified\":false,\"automaticRetry\":false,\"nextAction\":\"reload_configuration\"}\n",
  state,may_change?"true":"false",matches?"true":"false",flash,notification);
}
static void do_wr_modern_guest_apply(const char *url,FILE *stream)
{
 struct wr_modern_guest_plan plan;
 enum wr_modern_guest_error reason;
 const char *version,*value,*desired;
 char key[40];unsigned int i;
 FILE *sink;int matches=1,changed,notify,manual;
 (void)url;memset(&plan,0,sizeof(plan));
 if(!wr_modern_guest_post_allowed()) {
  wr_modern_guest_reply(stream,"rejected",0,0,"not_requested","not_requested");return;
 }
 if(nvram_modified||restart_needed_bits||rt_modified||wl_modified) {
  wr_modern_guest_reply(stream,"busy",0,0,"not_requested","not_requested");return;
 }
 version=wr_shared_cgi_read((void *)stream,"wr_modern_guest_version");
 if(!version||wr_modern_guest_admit_reason(&plan,wr_shared_cgi_read,wr_shared_nv_read,
                (void *)stream,&reason)!=WR_SHARED_WIFI_OK) {
  wr_modern_guest_reply(stream,version&&reason==WR_GUEST_ERROR_RELOAD?"reload_required":"rejected",0,0,"not_requested","not_requested");
  wr_modern_guest_clear(&plan);return;
 }
 sink=fopen("/dev/null","w");
 if(!sink) {
  wr_modern_guest_reply(stream,"unavailable",0,0,"not_requested","not_requested");
  wr_modern_guest_clear(&plan);return;
 }
 wr_modern_guest_finish_seen=0;
 update_variables_ex(0,sink,0,NULL);
 if(!wr_modern_guest_finish_seen) {
  fclose(sink);wr_modern_guest_clear(&plan);
  wr_modern_guest_reply(stream,"reload_required",0,0,"not_requested","not_requested");return;
 }
 for(i=0;i<13;i++) {
  snprintf(key,sizeof(key),"%s_guest_%s",plan.band,wr_modern_guest_fields[i]);
  desired=wr_shared_cgi_read((void *)stream,key);value=nvram_safe_get(key);
  if(!desired||!value||strcmp(desired,value))matches=0;
 }
 if(plan.has_key) {
  snprintf(key,sizeof(key),"%s_guest_wpa_psk",plan.band);
  value=nvram_safe_get(key);if(!value||strcmp(value,plan.key))matches=0;
 }
 if(!matches) {
  /* Own request only: entry refused pending HTTP changes. No delayed notification
   * may escape an unconfirmed partial write; this does not roll back NVRAM. */
  nvram_modified=0;restart_needed_bits=0;rt_modified=wl_modified=0;
  fclose(sink);wr_modern_guest_clear(&plan);
  wr_modern_guest_reply(stream,"unconfirmed",1,0,"not_requested","not_requested");return;
 }
 changed=nvram_modified!=0;notify=restart_needed_bits!=0;manual=nvram_get_int("nvram_manual")==1;
 asus_nvram_commit(0,sink,0,NULL);ej_notify_services(0,sink,0,NULL);
 fclose(sink);wr_modern_guest_clear(&plan);
 wr_modern_guest_reply(stream,"configuration_matches",changed,1,
  !changed?"not_requested":manual?"manual_mode":"requested_unverified",
  notify?"requested_unverified":"not_requested");
}
