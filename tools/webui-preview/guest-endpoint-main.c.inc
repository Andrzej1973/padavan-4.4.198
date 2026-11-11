static void reset_endpoint(int shared,int manual)
{
 used=writes=nvram_modified=auth_nvram_changed=rt_modified=wl_modified=0;
 commits=notify2=notify5=response_done=response_unchanged=response_errors=0;restart_needed_bits=0;
 nvram_set("wr_wifi_shared",shared?"1":"0");nvram_set("nvram_manual",manual?"1":"0");
 nvram_set("rt_ssid","Main24");nvram_set("wl_ssid","Main5");nvram_set("rt_channel","6");nvram_set("wl_channel","44");
 nvram_set("rt_wpa_psk","main24-password");nvram_set("wl_wpa_psk","main5-password");
 nvram_set("rt_guest_ssid","Before24");nvram_set("wl_guest_ssid","Before5");
 nvram_set("rt_guest_wpa_psk","guest24-password");nvram_set("wl_guest_wpa_psk","guest5-password");writes=0;
}
static void endpoint_request(const char *body,int declared,int auth)
{
 FILE *stream=tmpfile();conn_item_t item={0};assert(stream);
 fprintf(stream,"POST /start_apply.htm HTTP/1.1\r\nHost: fixture\r\nContent-Length: %d\r\nX-WR-Modern: 1\r\n%s\r\n%s",declared,auth?"Authorization: Basic fixture-good\r\n":"",body);
 rewind(stream);inputs=outputs=observed=status_code=auth_calls=0;login_fixture=3;
 handle_request(stream,&item);fclose(stream);
}
static void make_body(char *out,size_t capacity,int band,int variant)
{
 const char *p=band?"wl":"rt",*service=band?"WLANConfig11a":"WLANConfig11b";
 snprintf(out,capacity,"wr_modern_guest_version=1&wr_modern_guest_band=%s&wr_modern_guest_password_intent=%s&sid_list=%s%%3B&action_mode=+Apply+&%s_guest_enable=1&%s_guest_ssid=Endpoint+Guest%%26%%D0%%94&%s_guest_closed=0&%s_guest_auth_mode=%s&%s_guest_wpa_mode=2&%s_guest_crypto=aes&%s_guest_lan_isolate=1&%s_guest_ap_isolate=1&%s_guest_macrule=0&%s_guest_mcs_mode=0&%s_guest_date_x=0111110&%s_guest_time_x=08002200&%s_guest_time2_x=10002300&rt_ssid=injected&rt_channel=13&scripts.test=injected",p,variant==1?"change":"keep",service,p,p,p,p,variant==2?"open":"psk",p,p,p,p,p,p,p,p,p);
 if(variant==1){char field[100];snprintf(field,sizeof(field),"&%s_guest_wpa_psk=endpoint-new-key",p);strcat(out,field);}
}
int main(void)
{
 char body[4096],bad[8192],key[40];
 for(int band=0;band<2;band++)for(int shared=0;shared<2;shared++)for(int manual=0;manual<2;manual++)for(int variant=0;variant<3;variant++){
  reset_endpoint(shared,manual);make_body(body,sizeof(body),band,variant);
  endpoint_request(body,(int)strlen(body),1);
  assert(status_code==200&&inputs==1&&outputs==1&&observed&&auth_calls==1&&!response_errors);
  snprintf(key,sizeof(key),"%s_guest_ssid",band?"wl":"rt");assert(!strcmp(nvram_safe_get(key),"Endpoint Guest&Д"));
  snprintf(key,sizeof(key),"%s_guest_wpa_psk",band?"wl":"rt");assert(!strcmp(nvram_safe_get(key),variant==1?"endpoint-new-key":band?"guest5-password":"guest24-password"));
  assert(!strcmp(nvram_safe_get("rt_ssid"),"Main24")&&!strcmp(nvram_safe_get("wl_ssid"),"Main5"));
  assert(!strcmp(nvram_safe_get("rt_channel"),"6")&&!strcmp(nvram_safe_get("wl_channel"),"44"));
  assert(!strcmp(nvram_safe_get(band?"rt_guest_ssid":"wl_guest_ssid"),band?"Before24":"Before5"));
  assert(commits==!manual&&notify2==!band&&notify5==band&&!get_cgi("wr_modern_guest_version"));
  for(size_t i=0;i<sizeof(post_buf);i++)assert(!post_buf[i]);
  int count=writes;endpoint_request(body,(int)strlen(body),1);assert(writes==count&&commits==!manual&&notify2==!band&&notify5==band);
 }
 reset_endpoint(1,0);make_body(body,sizeof(body),0,0);
 snprintf(bad,sizeof(bad),"%s&rt_guest_enable=0",body);
 endpoint_request(bad,(int)strlen(bad),1);assert(status_code==400&&!outputs&&!writes&&!commits&&!notify2);
 endpoint_request(body,(int)strlen(body)+3,1);assert(status_code==400&&!outputs&&!writes&&!commits);
 endpoint_request(body,(int)strlen(body),0);assert(status_code==401&&!inputs&&!outputs&&!writes&&!commits);
 init_cgi(NULL);
 puts("PASS joined actual HTTP->body->CGI->update/apply->commit/notify:24 endpoint cases+replay, UTF8, injection, rejected duplicate/short/unauth; auth/NVRAM/template-order substitutes, not sockets/device");return 0;
}
