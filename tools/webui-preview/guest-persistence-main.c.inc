/* Host fixture only; actual apply/commit/notify functions precede this. */
static const char *guest_values[]={"1","Accepted Guest","0","psk","2","aes","1","1","0","0","0111110","08002200","10002300"};
static char *guest_cgi(webs_t wp,char *name,char *fallback)
{
 char key[40];unsigned int i;(void)wp;
 if(!strcmp(name,"wr_modern_guest_version"))return "1";
 if(!strcmp(name,"wr_modern_guest_band"))return source_band?"wl":"rt";
 if(!strcmp(name,"wr_modern_guest_password_intent"))return posted_key?"change":"keep";
 if(!strcmp(name,"action_mode"))return " Apply ";
 if(!strcmp(name,"action_script"))return "";
 if(!strcmp(name,"sid_list"))return source_band?"WLANConfig11a;":"WLANConfig11b;";
 for(i=0;i<13;i++){
  snprintf(key,sizeof(key),"%s_guest_%s",source_band?"wl":"rt",wr_modern_guest_fields[i]);
  if(!strcmp(key,name))return (char *)guest_values[i];
 }
 snprintf(key,sizeof(key),"%s_guest_wpa_psk",source_band?"wl":"rt");if(!strcmp(key,name))return (char *)posted_key;
 if(!strcmp(name,"wr_modern_wifi_version")||!strcmp(name,"wr_wifi_shared")||!strcmp(name,"wr_wifi_source"))return fallback;
 /* Every non-Guest table name is maliciously submitted. */
 for(int band=0;band<2;band++)for(struct variable *v=GetVariables(band);v->name;v++){
  if(!strcmp(v->name,name)&&strncmp(name,"rt_guest_",9)&&strncmp(name,"wl_guest_",9))return "injected";
 }
 return fallback;
}
static void guest_exercise(int shared,int change,int manual,int band,int open)
{
 struct wr_modern_password_context modern={0};struct wr_shared_wifi_adapter plan;
 char key[40];int count;
 (void)wr_modern_password_request;
 used=writes=nvram_modified=auth_nvram_changed=rt_modified=wl_modified=0;restart_needed_bits=0;
 source_band=band;shared_mode=shared;posted_key=change?"changed-guest-key":NULL;commits=notify2=notify5=0;
 guest_values[3]=open?"open":"psk";
 nvram_set("wr_wifi_shared",shared?"1":"0");nvram_set("nvram_manual",manual?"1":"0");
 nvram_set("rt_ssid","Main24");nvram_set("wl_ssid","Main5");nvram_set("rt_wpa_psk","Main24-secret");nvram_set("wl_wpa_psk","Main5-secret");
 nvram_set("rt_guest_ssid","Old24");nvram_set("wl_guest_ssid","Old5");
 nvram_set("rt_guest_wpa_psk","Guest24-secret");nvram_set("wl_guest_wpa_psk","Guest5-secret");
 nvram_set("rt_channel","6");nvram_set("wl_channel","44");writes=0;
 modern.wp=NULL;
 assert(wr_modern_guest_admit(&modern.guest,wr_shared_cgi_read,wr_shared_nv_read,NULL)==WR_SHARED_WIFI_OK);modern.guest_active=1;
 assert(wr_shared_wifi_prepare(&plan,&modern,wr_modern_cgi_read,wr_modern_nv_read)==WR_SHARED_WIFI_OK);
 assert(plan.plan.mode==WR_SHARED_INDEPENDENT);
 assert(validate_asp_apply(NULL,band,&plan,&modern)==1);
 assert(!strcmp(nvram_safe_get("rt_ssid"),"Main24")&&!strcmp(nvram_safe_get("wl_ssid"),"Main5"));
 assert(!strcmp(nvram_safe_get("rt_wpa_psk"),"Main24-secret")&&!strcmp(nvram_safe_get("wl_wpa_psk"),"Main5-secret"));
 assert(!strcmp(nvram_safe_get("wr_wifi_shared"),shared?"1":"0"));
 assert(!strcmp(nvram_safe_get(band?"rt_guest_ssid":"wl_guest_ssid"),band?"Old24":"Old5"));
 for(unsigned int i=0;i<13;i++){
  snprintf(key,sizeof(key),"%s_guest_%s",band?"wl":"rt",wr_modern_guest_fields[i]);
  assert(!strcmp(nvram_safe_get(key),guest_values[i]));
 }
 snprintf(key,sizeof(key),"%s_guest_ssid",band?"wl":"rt");assert(!strcmp(nvram_safe_get(key),"Accepted Guest"));
 snprintf(key,sizeof(key),"%s_guest_wpa_psk",band?"wl":"rt");
 assert(!strcmp(nvram_safe_get(key),change?"changed-guest-key":band?"Guest5-secret":"Guest24-secret"));
 assert(!strcmp(nvram_safe_get("rt_channel"),"6")&&!strcmp(nvram_safe_get("wl_channel"),"44")&&!*nvram_safe_get("scripts.test"));
 assert(restart_needed_bits==(band?2U:1U));assert(!auth_nvram_changed);
 count=writes;assert(validate_asp_apply(NULL,band,&plan,&modern)==1);assert(writes==count);
 asus_nvram_commit(0,NULL,0,NULL);assert(commits==(manual?0:1));
 ej_notify_services(0,NULL,0,NULL);assert(notify2==!band&&notify5==band&&!restart_needed_bits);
 asus_nvram_commit(0,NULL,0,NULL);ej_notify_services(0,NULL,0,NULL);assert(commits==(manual?0:1)&&notify2==!band&&notify5==band);
 wr_modern_guest_clear(&modern.guest);
}
int main(void)
{
 for(int band=0;band<2;band++)for(int shared=0;shared<2;shared++)for(int manual=0;manual<2;manual++){
  guest_exercise(shared,0,manual,band,0);guest_exercise(shared,1,manual,band,0);guest_exercise(shared,0,manual,band,1);
 }
 puts("PASS actual Guest apply/commit/notify:24 band/shared/manual/keep/change/open cases, Main/other Guest/radio preserved, replay no extra writes/notify; host substitutes only");return 0;
}
