#include "wcid-fifo-retirement.h"
#include <assert.h>
#include <string.h>
#include <stdio.h>
int main(void){
 unsigned int state,head,tail,i,checked=0;
 /* Exhaust every 4-slot layout, every pair of ring indices and both peers.
  * Equal indices cover full as well as empty layouts. */
 for(state=0;state<81;state++)for(head=0;head<4;head++)for(tail=0;tail<4;tail++){
  unsigned char before[4],after[4],peer;
  unsigned int v=state,w;
  for(i=0;i<4;i++){before[i]=(unsigned char)(v%3);v/=3;}
  for(w=1;w<=2;w++){
   unsigned int d=head,removed=99,expected=0,pos,n;
   memcpy(after,before,4);
   assert(wr_iot_wcid_fifo_retire(after,4,&d,tail,(unsigned char)w,&removed));
   for(i=0;i<4;i++){
    if(before[i]==w){expected++;assert(after[i]==0);}
    else assert(after[i]==before[i]);
   }
   assert(removed==expected);
   pos=head;for(n=0;n<4&&!after[pos];n++)pos=(pos+1)%4;
   assert(d==(n==4?tail:pos));
   assert(wr_iot_wcid_fifo_head(after,4,&d,tail,&peer)==(n==4?0:1));
   assert(peer==(n==4?0:after[pos]));
   /* Repeating cleanup is idempotent and cannot move survivor indices. */
   assert(wr_iot_wcid_fifo_retire(after,4,&d,tail,(unsigned char)w,&removed));
   assert(!removed);checked++;
  }
 }
 {unsigned char t[2]={1,2},saved[2],peer=9;unsigned int d=2,n=7;
  memcpy(saved,t,2);assert(!wr_iot_wcid_fifo_retire(t,2,&d,0,1,&n));
  assert(!memcmp(t,saved,2)&&n==7&&d==2);
  d=0;assert(!wr_iot_wcid_fifo_retire(t,2,&d,0,0,&n));
  assert(wr_iot_wcid_fifo_head(t,0,&d,0,&peer)==-1&&peer==9);
 }
 printf("PASS %u FIFO retirement layouts; no source binding or DMA proof\n",checked);
 return 0;
}
