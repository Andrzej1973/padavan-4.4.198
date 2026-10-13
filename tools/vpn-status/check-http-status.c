#define BOARD_WR1200JS 1
#include <stdio.h>
#include <stdarg.h>
#include <assert.h>
#include <string.h>
typedef FILE *webs_t;
static long current_uptime=100;
static long uptime(void){return current_uptime;}
static char output[512];
static int append_output;
static int websWrite(webs_t wp,const char *format,...)
{
 int result;va_list args;(void)wp;va_start(args,format);
 {size_t offset=append_output?strlen(output):0;
 result=vsnprintf(output+offset,sizeof(output)-offset,format,args);}
 va_end(args);return result;
}
static int ej_wr_vpn_interface_state(int eid,webs_t wp,int argc,char **argv)
{(void)eid;(void)argc;(void)argv;return websWrite(wp,"3");}
#include "http-status.inc"
int main(void)
{
 char *client[]={"client"},*server[]={"server"},*invalid[]={"invalid"};
 struct wr_handshake_observation observation={0};
 ej_wr_vpn_handshake_state(0,NULL,1,client);assert(!strcmp(output,"{\"state\":0}"));
 observation.peers=2;observation.recent=1;observation.never=1;
 wr_handshake_cache_publish(&wr_vpn_runtime[0].cache,100,1,&observation);
 ej_wr_vpn_handshake_state(0,NULL,1,client);assert(strstr(output,"\"state\":1"));assert(strstr(output,"\"peers\":2"));
 ej_wr_vpn_handshake_state(0,NULL,1,server);assert(!strcmp(output,"{\"state\":0}"));
 ej_wr_vpn_handshake_state(0,NULL,1,invalid);assert(!strcmp(output,"{\"state\":0}"));
 current_uptime=161;
 ej_wr_vpn_handshake_state(0,NULL,1,client);assert(strstr(output,"\"state\":2"));
 assert(strstr(output,"\"sample_age\":61"));
 output[0]=0;append_output=1;
 ej_wr_vpn_status(0,NULL,1,client);
 assert(strstr(output,"{\"interface\":3,\"handshake\":{\"state\":2"));
 assert(output[strlen(output)-1]=='}'&&output[strlen(output)-2]=='}');
 wr_vpn_background_close();
 puts("PASS VPN HTTP observation roles, missing data and stale sample");return 0;
}
