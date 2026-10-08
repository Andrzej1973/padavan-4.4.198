#include "adapter.h"
#include <assert.h>
#include <stdio.h>
struct item{const char *key,*value;};
struct fixture{struct item *cgi;};
static const char *read_cgi(void *ctx,const char *key){struct fixture *f=ctx;int i;for(i=0;f->cgi[i].key;i++)if(!strcmp(key,f->cgi[i].key))return f->cgi[i].value;return NULL;}
static const char *read_nv(void *ctx,const char *key){(void)ctx;return !strcmp(key,"wr_wifi_shared")?"0":!strncmp(key,"rt_",3)?"old-2g":"old-5g";}
int main(void){
 struct item cgi[]={{"wr_wifi_shared","1"},{"wr_wifi_source","rt"},{"sid_list","WLANConfig11b;WLANConfig11a;"},{"rt_ssid","Home"},{"rt_auth_mode","psk"},{"rt_wep_x","0"},{"rt_wpa_mode","2"},{"rt_crypto","aes"},{"rt_wpa_psk","password"},{NULL,NULL}};
 struct fixture f={cgi};struct wr_shared_wifi_adapter a,before;
 memset(&a,0x5a,sizeof(a));before=a;
 assert(wr_shared_wifi_prepare(&a,&f,read_cgi,read_nv)==WR_SHARED_WIFI_OK);
 assert(!strcmp(wr_shared_wifi_value(&a,"wl_ssid",NULL),"Home"));
 assert(!strcmp(wr_shared_wifi_value(&a,"wl_wpa_psk",NULL),"password"));
 assert(wr_shared_wifi_value(&a,"wl_ssid2","forged")==NULL);
 assert(!strcmp(wr_shared_wifi_value(&a,"wl_channel","40"),"40"));
 cgi[2].value="WLANConfig11b;FakeWLANConfig11a;";a=before;
 assert(wr_shared_wifi_prepare(&a,&f,read_cgi,read_nv)==WR_SHARED_WIFI_MISSING);assert(!memcmp(&a,&before,sizeof(a)));
 cgi[2].value="WLANConfig11b;WLANConfig11a;";cgi[8].value="short";
 assert(wr_shared_wifi_prepare(&a,&f,read_cgi,read_nv)==WR_SHARED_WIFI_PASSWORD);assert(!memcmp(&a,&before,sizeof(a)));
 cgi[0].value="0";assert(wr_shared_wifi_prepare(&a,&f,read_cgi,read_nv)==WR_SHARED_WIFI_OK);
 assert(!strcmp(wr_shared_wifi_value(&a,"rt_ssid","changed"),"old-2g"));
 assert(!strcmp(wr_shared_wifi_value(&a,"wl_ssid2","forged"),"old-5g"));
 assert(!strcmp(wr_shared_wifi_value(&a,"wr_wifi_shared",NULL),"0"));
 assert(!wr_shared_wifi_service("BadWLANConfig11a;","WLANConfig11a"));
 puts("PASS shared Wi-Fi CGI adapter: exact services, coherent fields, disable snapshots, encoded SSID protection, unchanged output on rejection");return 0;
}
