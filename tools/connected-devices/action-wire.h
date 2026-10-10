#ifndef WR_ACTION_WIRE_H
#define WR_ACTION_WIRE_H
#include "action-event.h"
#include <string.h>
#define WR_ACTION_WIRE_SIZE 48
static inline uint64_t wr_action_read(const unsigned char *p,unsigned int n){uint64_t v=0;unsigned int i;for(i=0;i<n;i++)v|=(uint64_t)p[i]<<(8*i);return v;}
static inline void wr_action_write(unsigned char *p,uint64_t v,unsigned int n){unsigned int i;for(i=0;i<n;i++)p[i]=(unsigned char)(v>>(8*i));}
/* Fixed wire layout; never memcpy a compiler-dependent C struct across ABI. */
static inline int wr_action_encode(const struct wr_action_event *e,unsigned char *p,size_t n){
 uint32_t result;
 if(!p||n!=WR_ACTION_WIRE_SIZE||!wr_action_valid(e))return 0;
 memset(p,0,n);p[0]='W';p[1]='R';p[2]='A';p[3]=1;
 p[4]=e->source;p[5]=e->stage;p[6]=e->radio;p[7]=e->bss;memcpy(p+8,e->mac,6);p[14]=e->operation;
 wr_action_write(p+16,e->session,8);wr_action_write(p+24,e->sequence,8);wr_action_write(p+32,e->uptime_ms,8);wr_action_write(p+40,e->cookie,4);
 result=(uint32_t)e->result;wr_action_write(p+44,result,4);return 1;
}
static inline int wr_action_decode(const unsigned char *p,size_t n,struct wr_action_event *out){
 struct wr_action_event e;uint32_t bits;int32_t result;
 if(!p||!out||n!=WR_ACTION_WIRE_SIZE||p[0]!='W'||p[1]!='R'||p[2]!='A'||p[3]!=1||p[15])return 0;
 memset(&e,0,sizeof(e));e.source=p[4];e.stage=p[5];e.radio=p[6];e.bss=p[7];memcpy(e.mac,p+8,6);e.operation=p[14];
 e.session=wr_action_read(p+16,8);e.sequence=wr_action_read(p+24,8);e.uptime_ms=wr_action_read(p+32,8);e.cookie=(uint32_t)wr_action_read(p+40,4);
 bits=(uint32_t)wr_action_read(p+44,4);memcpy(&result,&bits,sizeof(result));e.result=result;
 if(!wr_action_valid(&e))return 0;
 *out=e;return 1;
}
#endif
