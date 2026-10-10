#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "rssi-record.h"
#include "rssi-identity.h"
#include "rssi-query-request.h"
int main(void)
{
 struct wr_rssi_records ring={0},before;
 struct wr_rssi_record e={0};unsigned int i;
 e.attempt=1;e.mac[0]=2;e.mac[5]=1;e.stage=WR_RSSI_DECISION;
 assert(wr_rssi_record_append(&ring,&e));
 e.mac[5]=0;assert(ring.entries[0].mac[5]==1);e.mac[5]=1;
 for(i=1;i<70;i++){e.uptime_ms=i;e.stage=1+i%4;assert(wr_rssi_record_append(&ring,&e));}
 assert(ring.count==64&&ring.next==6&&ring.overwritten==6&&ring.sequence==70);
 assert(ring.entries[ring.next].sequence==7);
 {
  struct wr_rssi_record out[64];int n;
  before=ring;n=wr_rssi_record_read(&ring,0,out,64);assert(n==64);
  for(i=0;i<64;i++)assert(out[i].sequence==7+i);
  assert(!memcmp(&ring,&before,sizeof ring));
  assert(wr_rssi_record_read(&ring,68,out,64)==2&&out[0].sequence==69&&out[1].sequence==70);
  assert(wr_rssi_record_read(&ring,0,out,1)==1&&out[0].sequence==7);
  assert(wr_rssi_record_read(&ring,70,out,64)==0);
  assert(wr_rssi_record_read(&ring,71,out,64)==-1);
  assert(wr_rssi_record_read(&ring,0,out,65)==-1);
  assert(wr_rssi_record_read(&ring,0,out,0)==-1);
  assert(wr_rssi_record_read(&ring,0,0,64)==-1);
 }
 before=ring;e.mac[0]=1;assert(!wr_rssi_record_append(&ring,&e));
 assert(!memcmp(&ring,&before,sizeof ring));e.mac[0]=2;
 e.stage=5;assert(!wr_rssi_record_append(&ring,&e));e.stage=1;
 e.attempt=0;assert(!wr_rssi_record_append(&ring,&e));e.attempt=1;
 e.bss=16;assert(!wr_rssi_record_append(&ring,&e));e.bss=0;
 e.radio=2;assert(!wr_rssi_record_append(&ring,&e));e.radio=0;
 memset(e.mac,0,6);assert(!wr_rssi_record_append(&ring,&e));e.mac[0]=2;
 ring.overwritten=~0ULL;assert(wr_rssi_record_append(&ring,&e));assert(ring.overwritten==~0ULL);
 ring.sequence=~0ULL;before=ring;assert(!wr_rssi_record_append(&ring,&e));assert(!memcmp(&ring,&before,sizeof ring));
 ring.sequence=1;ring.next=64;assert(!wr_rssi_record_append(&ring,&e));
 assert(!wr_rssi_record_append(0,&e));assert(!wr_rssi_record_append(&ring,0));
 puts("PASS bounded RSSI records, copied identity, stages, overflow and rejected-input immutability");
 {
  struct wr_rssi_records attempts={0},saved;
  struct wr_rssi_record identity={0};identity.mac[0]=2;
  assert(wr_rssi_record_begin(&attempts,&identity));
  assert(identity.attempt==1&&identity.stage==WR_RSSI_DECISION);
  assert(wr_rssi_record_begin(&attempts,&identity)&&identity.attempt==2);
  identity.mac[0]=1;saved=attempts;
  assert(!wr_rssi_record_begin(&attempts,&identity));assert(!memcmp(&attempts,&saved,sizeof saved));
  identity.mac[0]=2;attempts.attempt_sequence=~0U;saved=attempts;
  assert(!wr_rssi_record_begin(&attempts,&identity));assert(!memcmp(&attempts,&saved,sizeof saved));
  assert(identity.attempt==2);
 }
 puts("PASS distinct RSSI attempt reservation, invalid identity and exhaustion without reuse");
 {
  unsigned long long births=0;unsigned char mac[6]={2,0,0,0,0,1};
  struct wr_rssi_identity first,recycled,saved;
  assert(wr_rssi_identity_create(&births,7,mac,&first));saved=first;
  assert(wr_rssi_identity_matches(&first,&saved));
  assert(wr_rssi_identity_create(&births,7,mac,&recycled));
  assert(!wr_rssi_identity_matches(&first,&recycled));
  saved.wcid=8;assert(!wr_rssi_identity_matches(&first,&saved));
  saved=first;saved.mac[5]=2;assert(!wr_rssi_identity_matches(&first,&saved));
  mac[0]=1;assert(!wr_rssi_identity_create(&births,7,mac,&saved));assert(births==2);
  births=~0ULL;mac[0]=2;assert(!wr_rssi_identity_create(&births,7,mac,&saved));
 }
 puts("PASS reused station slot and identical MAC rejected by client birth identity");
 {
  unsigned char buffer[41]={0},*q=buffer+1;
  struct wr_rssi_query_request request={0},saved;
  memcpy(q,"WRSQ",4);q[4]=1;q[6]=64;q[8]=1;
  assert(wr_rssi_query_decode(q,40,&request));assert(request.capacity==64&&request.radio==1);
  saved=request;q[9]=1;
  assert(!wr_rssi_query_decode(q,40,&request));assert(!memcmp(&saved,&request,sizeof saved));q[9]=0;
  q[16]=1;assert(!wr_rssi_query_decode(q,40,&request));
  q[24]=2;assert(wr_rssi_query_decode(q,40,&request)&&request.after==1&&request.session[0]==2);
  q[6]=65;assert(!wr_rssi_query_decode(q,40,&request));q[6]=64;
  assert(!wr_rssi_query_decode(q,39,&request));assert(!wr_rssi_query_decode(q,41,&request));
  assert(!wr_rssi_query_decode(0,40,&request));assert(!wr_rssi_query_decode(q,40,0));
 }
 puts("PASS RSSI request fixed encoding, unaligned input, bounds and invalid-output immutability");
 return 0;
}
