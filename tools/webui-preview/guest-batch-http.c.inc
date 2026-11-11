/* Isolated candidate: uses existing service metadata and commit/notify APIs.
 * No per-field SET, update_variables_ex fallback or automatic retry. */
struct wr_guest_batch_effects {u64 events,key_events;unsigned int flags,public_changes;int key_set;};
static int wr_guest_batch_effects(const struct wr_nvram_wire_request *packet,
                                struct wr_guest_batch_effects *out)
{
 struct wr_guest_batch_effects next={0};struct variable *table,*v;
 const char *service;int sid;unsigned int i;u64 allowed;
 const struct wr_nvram_wire_item *item;
 int band=!strncmp(packet->items[0].name,"wl_",3);
 allowed=band?EVM_RESTART_WIFI5:EVM_RESTART_WIFI2;
 for(sid=0;(service=GetServiceId(sid))!=NULL;sid++)
  if(!strcmp(service,band?"WLANConfig11a":"WLANConfig11b"))break;
 if(!service)return 0;
 table=GetVariables(sid);if(!table)return 0;
 for(i=0;i<packet->count;i++){
  item=&packet->items[i];
  for(v=table;v->name&&strcmp(v->name,item->name);v++){}
  if(!v->name||((v->event_mask&EVM_BLOCK_UNSAFE)&&!get_login_safe())||
     (v->event_mask&~(allowed|EVM_BLOCK_UNSAFE)))return 0;
  if(!(item->flags&2U))continue;
  if(i==13){next.key_set=1;next.key_events=v->event_mask&allowed;continue;}
  if(!strcmp(item->expected,item->value))continue;
  next.public_changes++;next.events|=v->event_mask&allowed;
  if(i==0||i==10||i==11||i==12)next.flags|=WIFI_GUEST_CONTROL_BIT;
  else next.flags|=WIFI_COMMON_CHANGE_BIT;
 }
 *out=next;return 1;
}
static void do_wr_modern_guest_apply(const char *url,FILE *stream)
{
 struct wr_nvram_wire_request packet={0};struct wr_guest_batch_effects effects={0};
 enum wr_modern_guest_error reason=WR_GUEST_ERROR_INVALID;
 const char *state="rejected",*flash="not_requested",*notification="not_requested",*stored,*desired;
 FILE *sink=NULL;int fd=-1,saved_errno=0,may_change=0,matches=0,manual,band;
 unsigned int changed=0,i,flags;u64 events;
 (void)url;
 if(!wr_modern_guest_post_allowed())goto done;
 if(nvram_modified||restart_needed_bits||rt_modified||wl_modified){state="busy";goto done;}
 if(wr_modern_guest_build_batch(&packet,wr_shared_cgi_read,wr_shared_nv_read,(void *)stream,&reason)!=WR_SHARED_WIFI_OK){
  state=reason==WR_GUEST_ERROR_RELOAD?"reload_required":"rejected";goto done;
 }
 if(!wr_guest_batch_effects(&packet,&effects))goto done;
 sink=fopen("/dev/null","w");if(!sink){state="unavailable";goto done;}
 fd=open("/dev/nvram",O_RDWR|O_CLOEXEC);if(fd<0){state="unavailable";goto done;}
 if(wr_nvram_submit_batch(fd,&packet,&changed)<0){
  saved_errno=errno;
  if(saved_errno==EAGAIN)state="reload_required";
  else if(saved_errno==EINVAL||saved_errno==ENOTTY||saved_errno==EPERM||saved_errno==ENOMEM||saved_errno==ENOSPC||saved_errno==EFAULT)state="unavailable";
  else {state="unconfirmed";may_change=1;}
  goto done;
 }
 may_change=changed!=0;
 if(changed<effects.public_changes||changed>effects.public_changes+(effects.key_set?1U:0U)){
  state="unconfirmed";may_change=1;goto done;
 }
 for(i=0;i<packet.count;i++){
  desired=(packet.items[i].flags&2U)?packet.items[i].value:packet.items[i].expected;
  stored=nvram_safe_get(packet.items[i].name);
  if(!stored||strcmp(stored,desired)){state="unconfirmed";may_change=1;goto done;}
 }
 /* Only this successful batch may populate deferred HTTP state. No legacy
  * writes run. Readback is an observation, not a lease against other writers. */
 flags=effects.flags;events=effects.events;
 if(effects.key_set&&changed>effects.public_changes){flags|=WIFI_COMMON_CHANGE_BIT;events|=effects.key_events;}
 band=!strncmp(packet.items[0].name,"wl_",3);
 nvram_modified=changed!=0;
 if(changed){restart_needed_bits=events;if(band)wl_modified=flags;else rt_modified=flags;}
 manual=nvram_get_int("nvram_manual")==1;
 asus_nvram_commit(0,sink,0,NULL);ej_notify_services(0,sink,0,NULL);
 matches=1;state="configuration_matches";
 flash=!changed?"not_requested":manual?"manual_mode":"requested_unverified";
 notification=changed&&events?"requested_unverified":"not_requested";
done:
 if(fd>=0)close(fd);
 if(sink)fclose(sink);
 wr_modern_guest_batch_wipe(&packet,sizeof(packet));
 wr_modern_guest_batch_wipe(&effects,sizeof(effects));
 wr_modern_guest_reply(stream,state,may_change,matches,flash,notification);
}
