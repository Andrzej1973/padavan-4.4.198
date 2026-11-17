#include "saved-config.h"
#include <assert.h>
#include <stdio.h>
struct fixture {const char *values[7];char borrowed[96];unsigned reads;};
static const char *read_fixture(void *context,const char *key)
{
 static const char *keys[]={"wr_iot_enable","wr_iot_ssid","wr_iot_psk",
  "wr_iot_gateway","wr_iot_mask","wr_iot_start","wr_iot_end"};
 struct fixture *f=context;size_t i;
 for(i=0;i<7;i++)if(!strcmp(keys[i],key)){
  f->reads++;if(!f->values[i])return NULL;
  strcpy(f->borrowed,f->values[i]);return f->borrowed;
 }
 assert(0);return NULL;
}
int main(void)
{
 struct fixture f={{"0","IoT: test $()","password:123","192.168.50.1",
  "255.255.255.0","192.168.50.20","192.168.50.200"},{0},0};
 struct wr_iot_saved_config config={0},decoded={0},before;
 struct wr_iot_request runtime={0};char record[WR_IOT_SAVED_CONFIG_MAX],bad[sizeof(record)];
 char tiny[4]="old";size_t length,i;struct wr_iot_range overlap;
 assert(wr_iot_saved_config_read(&config,read_fixture,&f,NULL,0)&&f.reads==7);
 assert(!config.profile.enabled&&!strcmp(config.profile.ssid,f.values[1]));
 assert(config.profile.subnet.network==0xc0a83200);
 assert(wr_iot_request_read(&runtime,read_fixture,&f,0,0,3,NULL,0));
 assert(!runtime.enabled&&!runtime.ssid[0]); /* Runtime OFF is deliberately different. */
 assert(wr_iot_saved_config_encode(record,sizeof(record),&config));length=strlen(record);
 assert(!strchr(record,'$')&&!strchr(record,' ')&&!strchr(record,'\n'));
 assert(wr_iot_saved_config_decode(&decoded,record,length));
 assert(!memcmp(&decoded,&config,sizeof(config)));
 assert(!wr_iot_saved_config_encode(tiny,sizeof(tiny),&config)&&!strcmp(tiny,"old"));
 memset(&decoded,0x5a,sizeof(decoded));before=decoded;
#define BAD() do {assert(!wr_iot_saved_config_decode(&decoded,bad,strlen(bad)));assert(!memcmp(&decoded,&before,sizeof(decoded)));} while(0)
 strcpy(bad,record);bad[0]='X';BAD();
 strcpy(bad,record);bad[strlen(WR_IOT_SAVED_CONFIG_VERSION)]='G';BAD();
 strcpy(bad,record);bad[strlen(WR_IOT_SAVED_CONFIG_VERSION)]='0';
 bad[strlen(WR_IOT_SAVED_CONFIG_VERSION)+1]='0';BAD(); /* Embedded NUL. */
 strcpy(bad,record);strcat(bad,":30");BAD();
 strcpy(bad,record);strcat(bad,":");BAD();
 strcpy(bad,record);bad[length-1]=0;BAD();
 strcpy(bad,WR_IOT_SAVED_CONFIG_VERSION);strcat(bad,"30::::::");BAD();
 for(i=0;i<length;i++){
  strcpy(bad,record);bad[i]='!';BAD();
 }
 /* Truncation either refuses unchanged or is a complete, independently valid
  * canonical profile (a shortened final IPv4 can itself be valid). */
 for(i=0;i<length;i++){
  int accepted=wr_iot_saved_config_decode(&decoded,record,i);
  if(accepted){ /* A truncated final IPv4 can only pass if it is a valid plan. */
   char canonical[sizeof(record)];assert(wr_iot_saved_config_encode(canonical,sizeof(canonical),&decoded));
   assert(strlen(canonical)==i&&!memcmp(canonical,record,i));
   decoded=before;
  }else assert(!memcmp(&decoded,&before,sizeof(decoded)));
 }
#undef BAD
 overlap.first=config.profile.subnet.network;overlap.last=config.profile.subnet.broadcast;
 assert(!wr_iot_saved_config_read(&decoded,read_fixture,&f,&overlap,1));
 assert(!memcmp(&decoded,&before,sizeof(decoded)));
 for(i=0;i<7;i++){
  const char *keep=f.values[i];f.values[i]=NULL;
  assert(!wr_iot_saved_config_read(&decoded,read_fixture,&f,NULL,0));
  assert(!memcmp(&decoded,&before,sizeof(decoded)));f.values[i]=keep;
 }
 f.values[0]="";assert(!wr_iot_saved_config_read(&decoded,read_fixture,&f,NULL,0));
 f.values[0]="2";assert(!wr_iot_saved_config_read(&decoded,read_fixture,&f,NULL,0));
 f.values[0]="0";f.values[2]="short";
 assert(!wr_iot_saved_config_read(&decoded,read_fixture,&f,NULL,0));
 f.values[2]="password123";f.values[4]="255.0.255.0";
 assert(!wr_iot_saved_config_read(&decoded,read_fixture,&f,NULL,0));
 f.values[4]="255.255.255.0";f.values[0]="1";
 f.values[1]="01234567890123456789012345678901";
 f.values[2]="0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef";
 assert(wr_iot_saved_config_read(&config,read_fixture,&f,NULL,0));
 assert(wr_iot_saved_config_encode(record,sizeof(record),&config));
 assert(wr_iot_saved_config_decode(&decoded,record,strlen(record)));
 assert(!memcmp(&decoded,&config,sizeof(config))&&decoded.profile.enabled);
 memset(config.profile.ssid,'x',sizeof(config.profile.ssid));
 assert(!wr_iot_saved_config_encode(record,sizeof(record),&config));
 puts("PASS saved IoT record: OFF retains validated credentials/subnet, borrowed reads copied, malformed/version/size/NUL/overlap refusal, canonical roundtrip and bounded PSK/SSID; codec only, no NVRAM/flash or runtime acceptance");
 return 0;
}
