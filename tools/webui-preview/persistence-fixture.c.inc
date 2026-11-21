/* Host-only framework/NVRAM substitutes. Generated helpers and the complete
 * actual validate_asp_apply function are inserted at the markers below. */
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#define BOARD_HAS_5G_RADIO 1
#define EVM_BLOCK_UNSAFE (1ULL<<63)
#define EVM_RESTART_WIFI2 1U
#define EVM_RESTART_WIFI5 2U
#define EVM_RESTART_REBOOT 1024U
#define WIFI_RADIO_CONTROL_BIT 16
#define RCN_RESTART_WIFI2 "restart_wifi2"
#define RCN_RESTART_WIFI5 "restart_wifi5"

#define WIFI_COMMON_CHANGE_BIT 1
#define WIFI_IWPRIV_CHANGE_BIT 2
#define WIFI_GUEST_CONTROL_BIT 4
#define WIFI_SCHED_CONTROL_BIT 8
#define IFNAME_2G_MAIN "ra0"
#define IFNAME_2G_GUEST "ra1"
#define IFNAME_5G_MAIN "rai0"
#define IFNAME_5G_GUEST "rai1"
#define STORAGE_DNSMASQ_DIR "/fixture/dns"
#define STORAGE_SCRIPTS_DIR "/fixture/scripts"
#define STORAGE_CRONTAB_DIR "/fixture/cron"
#define dbG(...) ((void)0)
typedef unsigned long long u64;
typedef void *webs_t;
struct variable {const char *name,*longname;void *unused;u64 event_mask;};
static struct variable table2[]={
 {"wr_wifi_shared","",NULL,3},{"rt_ssid","",NULL,1},{"rt_ssid2","",NULL,1},
 {"rt_auth_mode","",NULL,1},{"rt_wep_x","",NULL,1},{"rt_wpa_mode","",NULL,1},
 {"rt_crypto","",NULL,1},{"rt_wpa_psk","",NULL,1},{"rt_channel","",NULL,1},
 {"rt_guest_ssid","",NULL,1},{"scripts.test","File",NULL,1},{NULL,NULL,NULL,0}};
static struct variable table5[]={
 {"wl_ssid","",NULL,2},{"wl_ssid2","",NULL,2},{"wl_auth_mode","",NULL,2},
 {"wl_wep_x","",NULL,2},{"wl_wpa_mode","",NULL,2},{"wl_crypto","",NULL,2},
 {"wl_wpa_psk","",NULL,2},{"wl_channel","",NULL,2},{"wl_guest_ssid","",NULL,2},
 {NULL,NULL,NULL,0}};
static struct variable *GetVariables(int sid){return sid?table5:table2;}
struct pair {char name[40],value[160];};
static struct pair store[64];static int used,writes,nvram_modified,auth_nvram_changed,rt_modified,wl_modified;
static u64 restart_needed_bits;
static int shared_mode,source_band;static const char *posted_key;
static char *nvram_safe_get(const char *name){int i;for(i=0;i<used;i++)if(!strcmp(store[i].name,name))return store[i].value;return "";}
static int nvram_set(const char *name,const char *value){int i;for(i=0;i<used;i++)if(!strcmp(store[i].name,name))break;assert(i<64);if(i==used)used++;assert(strlen(name)<40&&strlen(value)<160);strcpy(store[i].name,name);strcpy(store[i].value,value);writes++;return 0;}
static int nvram_get_int(const char *name){return atoi(nvram_safe_get(name));}
static int nvram_set_int(const char *name,int value){char text[32];snprintf(text,sizeof(text),"%d",value);return nvram_set(name,text);}
static char *websGetVar(webs_t wp,char *name,char *fallback){(void)wp;
 if(!strcmp(name,"wr_modern_wifi_version"))return "1";
 if(!strcmp(name,"wr_modern_wifi_band"))return source_band?"wl":"rt";
 if(!strcmp(name,"wr_modern_expected_shared"))return shared_mode?"1":"0";
 if(!strcmp(name,"wr_modern_password_intent"))return posted_key?"change":"keep";
 if(!strcmp(name,"action_mode"))return " Apply ";
 if(!strcmp(name,"action_script"))return "";
 if(!strcmp(name,"sid_list"))return shared_mode?"WLANConfig11b;WLANConfig11a;":source_band?"WLANConfig11a;":"WLANConfig11b;";
 if(!strcmp(name,source_band?"wl_ssid":"rt_ssid"))return "Stored";
 if(!strcmp(name,source_band?"wl_auth_mode":"rt_auth_mode"))return "psk";
 if(!strcmp(name,source_band?"wl_wep_x":"rt_wep_x"))return "0";
 if(!strcmp(name,source_band?"wl_wpa_mode":"rt_wpa_mode"))return "2";
 if(!strcmp(name,source_band?"wl_crypto":"rt_crypto"))return "aes";
 if(!strcmp(name,source_band?"wl_wpa_psk":"rt_wpa_psk"))return (char *)posted_key;
 if(!strcmp(name,"rt_ssid2")||!strcmp(name,"rt_channel")||!strcmp(name,"wl_channel")||!strcmp(name,"rt_guest_ssid")||!strcmp(name,"wl_guest_ssid")||!strcmp(name,"scripts.test"))return "injected";
 return fallback;}
static int get_login_safe(void){return 1;}
static int write_textarea_to_file(const char *v,const char *d,const char *n){(void)v;(void)d;(void)n;abort();return 0;}
static int doSystem(const char *s,...){(void)s;abort();return 0;}
static const char *find_wlan_if_up(int band){(void)band;abort();return NULL;}
static void set_wifi_param_int(const char *i,const char *n,const char *v,int a,int b){(void)i;(void)n;(void)v;(void)a;(void)b;abort();}
static void brport_set_m2u(const char *i,int v){(void)i;(void)v;abort();}
static void set_wifi_mrate(const char *i,const char *v,int b){(void)i;(void)v;(void)b;abort();}
static void recreate_passwd_unix(int n){(void)n;abort();}
static void change_passwd_unix(const char *u,const char *p){(void)u;(void)p;abort();}
static void validate_nvram_lan_subnet(void){abort();}
/* Only delegation is checked; this substitutes, and does not verify, the encoder. */
static void char_to_ascii(char *out,const char *in){snprintf(out,160,"encoded:%s",in);}
static int commits,notify2,notify5;
struct event_fixture {const char *notify_cmd;u64 event_mask,event_unmask;};
static struct event_fixture events_desc[]={{NULL,0,0}};
static void nvram_commit(void){commits++;}
static void sys_reboot(void){abort();}
static void notify_rc(const char *command){if(!strcmp(command,RCN_RESTART_WIFI2))notify2++;else if(!strcmp(command,RCN_RESTART_WIFI5))notify5++;else abort();}
static int nvram_set_int_temp(const char *name,int value){return nvram_set_int(name,value);}
/* GENERATED_HELPERS */
/* GENERATED_APPLY */
static void reset(int shared){used=writes=nvram_modified=auth_nvram_changed=rt_modified=wl_modified=0;restart_needed_bits=0;shared_mode=shared;posted_key=NULL;
 nvram_set("wr_wifi_shared",shared?"1":"0");nvram_set("rt_ssid","Before-2g");nvram_set("wl_ssid","Before-5g");
 nvram_set("rt_wpa_psk","stored-passphrase");nvram_set("wl_wpa_psk","other-passphrase");
 nvram_set("rt_channel","6");nvram_set("wl_channel","44");nvram_set("rt_guest_ssid","Guest2");nvram_set("wl_guest_ssid","Guest5");writes=0;}
static void exercise(int shared,int change,int manual,int band){struct wr_modern_password_context modern={0};struct wr_shared_wifi_adapter plan;int count,b;
 const char *secret=change?"new-passphrase":band?"other-passphrase":"stored-passphrase";
 source_band=band;reset(shared);commits=notify2=notify5=0;nvram_set("nvram_manual",manual?"1":"0");writes=0;if(change)posted_key="new-passphrase";modern.wp=NULL;modern.band=band?"wl":"rt";
 assert(wr_modern_password_request(&modern.password,wr_shared_cgi_read,wr_shared_nv_read,NULL)==WR_SHARED_WIFI_OK);modern.active=1;
 assert(wr_shared_wifi_prepare(&plan,&modern,wr_modern_cgi_read,wr_modern_nv_read)==WR_SHARED_WIFI_OK);
 for(b=0;b<2;b++)if(shared||b==band)assert(validate_asp_apply(NULL,b,&plan,&modern)==1);
 assert(!strcmp(nvram_safe_get("rt_ssid"),shared||band==0?"Stored":"Before-2g"));
 assert(!strcmp(nvram_safe_get("wl_ssid"),shared||band==1?"Stored":"Before-5g"));
 assert(!strcmp(nvram_safe_get("rt_wpa_psk"),shared||band==0?secret:"stored-passphrase"));
 assert(!strcmp(nvram_safe_get("wl_wpa_psk"),shared||band==1?secret:"other-passphrase"));
 if(shared||band==0)assert(!strcmp(nvram_safe_get("rt_ssid2"),"encoded:Stored"));
 if(shared||band==1)assert(!strcmp(nvram_safe_get("wl_ssid2"),"encoded:Stored"));
 assert(!strcmp(nvram_safe_get("rt_channel"),"6")&&!strcmp(nvram_safe_get("wl_channel"),"44"));
 assert(!strcmp(nvram_safe_get("rt_guest_ssid"),"Guest2")&&!strcmp(nvram_safe_get("wl_guest_ssid"),"Guest5"));
 assert(!*nvram_safe_get("scripts.test"));assert(!auth_nvram_changed);assert(restart_needed_bits==(shared?3U:band?2U:1U));
 count=writes;for(b=0;b<2;b++)if(shared||b==band)assert(validate_asp_apply(NULL,b,&plan,&modern)==1);assert(writes==count);
 asus_nvram_commit(0,NULL,0,NULL);assert(commits==(manual?0:1));assert(nvram_modified==0);
 ej_notify_services(0,NULL,0,NULL);assert(notify2==(shared||band==0) && notify5==(shared||band==1));assert(!restart_needed_bits && !rt_modified && !wl_modified);
 asus_nvram_commit(0,NULL,0,NULL);ej_notify_services(0,NULL,0,NULL);assert(commits==(manual?0:1) && notify2==(shared||band==0) && notify5==(shared||band==1));
 wr_modern_password_clear(&modern.password);}
int main(void){int manual,band;for(band=0;band<2;band++)for(manual=0;manual<2;manual++){exercise(0,0,manual,band);exercise(0,1,manual,band);exercise(1,0,manual,band);exercise(1,1,manual,band);}puts("PASS complete actual apply/commit/notify: 16 both-source-band keep/change/shared/manual scenarios; other band/guest/radio preserved; host substitutes only");return 0;}
