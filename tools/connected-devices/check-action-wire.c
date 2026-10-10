#include "action-wire.h"
#include <assert.h>
#include <stdio.h>
int main(void){struct wr_action_event e={0},decoded={0},before;unsigned char p[48];size_t i;
 e.session=0x123456789ULL;e.sequence=7;e.uptime_ms=5000;e.source=WR_ACTION_RSSI;e.operation=WR_ACTION_KICK;e.stage=WR_ACTION_ALLOC_FAILED;e.mac[0]=2;e.result=-12;e.cookie=99;
 assert(wr_action_encode(&e,p,sizeof(p)));assert(p[16]==0x89&&p[17]==0x67&&p[24]==7);
 assert(wr_action_decode(p,sizeof(p),&decoded));assert(decoded.session==e.session&&decoded.result==-12&&decoded.cookie==99);before=decoded;
 for(i=0;i<sizeof(p);i++){assert(!wr_action_decode(p,i,&decoded));assert(!memcmp(&decoded,&before,sizeof(decoded)));}
 p[15]=1;assert(!wr_action_decode(p,sizeof(p),&decoded));p[15]=0;p[3]=2;assert(!wr_action_decode(p,sizeof(p),&decoded));
 puts("PASS fixed action wire format, signed result and atomic malformed-message rejection");return 0;}
