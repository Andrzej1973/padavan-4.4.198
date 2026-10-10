#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "rssi-record.h"
#include "rssi-identity.h"
#include "rssi-query-request.h"
#include "rssi-query-record.h"
#include "rssi-query-response.h"
#include "rssi-query-decode.h"
#include "rssi-query-client.h"
#include "rssi-history.h"
#include "rssi-collector.h"
static int fake_rssi_query(const char *name,int command,struct iwreq *r,void *context)
{
 int mode=*(int *)context;unsigned long long session[2]={11,22};struct wr_rssi_query_request q;
 struct wr_rssi_record record={0};unsigned int size;
 assert(!strcmp(name,"ra0")&&command==WR_RSSI_READ_IOCTL&&r->u.data.flags==WR_RSSI_READ_OID);
 assert(wr_rssi_query_decode(r->u.data.pointer,40,&q));if(mode==1){errno=ESTALE;return -1;}
 record.sequence=q.after+1;record.attempt=1;record.mac[0]=2;record.radio=q.radio;record.stage=1;
 if(mode==2)session[1]=23;
 size=wr_rssi_query_response_encode(r->u.data.pointer,r->u.data.length,session,record.sequence,0,q.radio,&record,1);
 assert(size==80);r->u.data.length=(mode==3)?79:80;return 0;
}
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
  {
   unsigned int i;unsigned char valid[40];
   memcpy(valid,q,40);saved=request;
   for(i=0;i<9;i++) {
    unsigned char old=q[i];q[i]=(i==6)?0:(unsigned char)(old+1);
    if(i==8)q[i]=2;
    assert(!wr_rssi_query_decode(q,40,&request));
    assert(!memcmp(&saved,&request,sizeof saved));q[i]=old;
   }
   for(i=9;i<16;i++) {
    q[i]=255;assert(!wr_rssi_query_decode(q,40,&request));
    assert(!memcmp(&saved,&request,sizeof saved));q[i]=0;
   }
   for(i=0;i<81;i++)if(i!=40) {
    assert(!wr_rssi_query_decode(q,i,&request));
    assert(!memcmp(&saved,&request,sizeof saved));
   }
   memset(q+16,255,24);
   assert(wr_rssi_query_decode(q,40,&request));
   assert(request.after==~0ULL&&request.session[0]==~0ULL&&request.session[1]==~0ULL);
   memcpy(q,valid,40);
  }
 }
 {
  struct wr_rssi_query_request q={0};unsigned long long session[2]={1,2};
  assert(wr_rssi_query_session_matches(&q,session));
  q.after=1;assert(!wr_rssi_query_session_matches(&q,session));
  q.session[0]=1;q.session[1]=2;assert(wr_rssi_query_session_matches(&q,session));
  session[1]=3;assert(!wr_rssi_query_session_matches(&q,session));
  session[0]=0;session[1]=0;assert(!wr_rssi_query_session_matches(&q,session));
  assert(!wr_rssi_query_session_matches(0,session));assert(!wr_rssi_query_session_matches(&q,0));
 }
 puts("PASS RSSI stale adapter session, initial cursor and invalid instance rejection");
 puts("PASS RSSI request fixed encoding, unaligned input, bounds and invalid-output immutability");
 {
  unsigned char out[34],saved[34];struct wr_rssi_record r={0};
  memset(out,0xa5,sizeof out);r.sequence=~0ULL;r.uptime_ms=0x0102030405060708ULL;
  r.attempt=0x11223344;r.mac[0]=2;r.mac[5]=3;r.radio=1;r.bss=15;r.stage=4;
  assert(wr_rssi_query_record_encode(out+1,32,&r));
  assert(out[0]==0xa5&&out[33]==0xa5&&out[1]==255&&out[9]==8&&out[16]==1);
  assert(out[17]==0x44&&out[20]==0x11&&out[21]==2&&out[26]==3);
  assert(out[27]==1&&out[28]==15&&out[29]==4&&!out[30]&&!out[31]&&!out[32]);
  memcpy(saved,out,sizeof out);r.stage=5;
  assert(!wr_rssi_query_record_encode(out+1,32,&r));assert(!memcmp(saved,out,sizeof out));
  r.stage=4;assert(!wr_rssi_query_record_encode(out+1,31,&r));
  assert(!memcmp(saved,out,sizeof out));assert(!wr_rssi_query_record_encode(0,32,&r));
 }
 puts("PASS fixed RSSI record byte layout, unaligned encoding and rejected-output immutability");
 {
  unsigned char out[113],saved[113];unsigned long long session[2]={1,2};
  struct wr_rssi_record records[2]={{0},{0}};unsigned int i;
  memset(out,0xa5,sizeof out);
  for(i=0;i<2;i++){records[i].sequence=i+1;records[i].attempt=i+1;records[i].mac[0]=2;records[i].stage=1;}
  assert(wr_rssi_query_response_encode(out+1,112,session,2,5,0,records,2)==112);
  assert(out[0]==0xa5&&out[1]=='W'&&out[7]==2&&out[9]==1&&out[17]==2&&out[25]==2&&out[33]==5);
  memcpy(saved,out,sizeof out);records[1].radio=1;
  assert(!wr_rssi_query_response_encode(out+1,112,session,2,5,0,records,2));
  assert(!memcmp(saved,out,sizeof out));records[1].radio=0;records[1].sequence=1;
  assert(!wr_rssi_query_response_encode(out+1,112,session,2,5,0,records,2));
  assert(!memcmp(saved,out,sizeof out));
  assert(wr_rssi_query_response_encode(out+1,48,session,0,0,0,0,0)==48);
  assert(!wr_rssi_query_response_encode(out+1,47,session,0,0,0,0,0));
 }
 {
  unsigned char out[WR_RSSI_QUERY_RESPONSE_MAX_BYTES+2],saved[WR_RSSI_QUERY_RESPONSE_MAX_BYTES+2];
  struct wr_rssi_record records[64];unsigned long long session[2]={~0ULL,~0ULL};unsigned int i;
  memset(records,0,sizeof records);memset(out,0xa5,sizeof out);
  for(i=0;i<64;i++) {
   records[i].sequence=i+1;records[i].attempt=i+1;records[i].mac[0]=2;
   records[i].mac[5]=(unsigned char)i;records[i].radio=1;records[i].bss=15;records[i].stage=4;
  }
  assert(wr_rssi_query_response_encode(out+1,2096,session,64,~0ULL,1,records,64)==2096);
  assert(out[0]==0xa5&&out[2097]==0xa5&&out[7]==64);
  {
   struct wr_rssi_query_response decoded={0},before;
   assert(wr_rssi_query_response_decode(out+1,2096,1,&decoded));
   assert(decoded.count==64&&decoded.records[63].attempt==64&&decoded.overwritten==~0ULL);
   before=decoded;out[1+48+63*32+29]=1;
   assert(!wr_rssi_query_response_decode(out+1,2096,1,&decoded));
   assert(!memcmp(&before,&decoded,sizeof decoded));out[1+48+63*32+29]=0;
   assert(!wr_rssi_query_response_decode(out+1,2095,1,&decoded));
   assert(!wr_rssi_query_response_decode(out+1,2096,0,&decoded));
   assert(!memcmp(&before,&decoded,sizeof decoded));
  }
  memcpy(saved,out,sizeof out);records[63].stage=5;
  assert(!wr_rssi_query_response_encode(out+1,2096,session,64,~0ULL,1,records,64));
  assert(!memcmp(saved,out,sizeof out));records[63].stage=4;
  assert(!wr_rssi_query_response_encode(out+1,2095,session,64,0,1,records,64));
  assert(!memcmp(saved,out,sizeof out));
  assert(!wr_rssi_query_response_encode(out+1,2096,session,64,0,1,records,65));
  assert(!memcmp(saved,out,sizeof out));
 }
 puts("PASS maximum 64-record RSSI response, buffer canaries and final-record preflight rejection");
 puts("PASS bounded RSSI response encoding, radio/sequence checks and all-input preflight");
 {
  unsigned char out[42],saved[42];
  struct wr_rssi_query_request q={0},decoded={0};
  q.capacity=64;q.radio=1;q.after=~0ULL;q.session[0]=~0ULL;q.session[1]=1;
  memset(out,0xa5,sizeof out);
  assert(wr_rssi_query_request_encode(out+1,40,&q));
  assert(out[0]==0xa5&&out[41]==0xa5);
  assert(wr_rssi_query_decode(out+1,40,&decoded));
  assert(decoded.after==q.after&&decoded.session[0]==q.session[0]&&decoded.session[1]==1&&decoded.radio==1&&decoded.capacity==64);
  memcpy(saved,out,sizeof out);q.capacity=65;
  assert(!wr_rssi_query_request_encode(out+1,40,&q));assert(!memcmp(saved,out,sizeof out));
  q.capacity=64;assert(!wr_rssi_query_request_encode(out+1,39,&q));assert(!memcmp(saved,out,sizeof out));
 }
 puts("PASS RSSI request encode/decode roundtrip, maximum values and invalid-output immutability");
 {
  struct wr_rssi_query_request q={0};struct wr_rssi_query_response out={0},before;int mode=0;
  q.capacity=64;assert(wr_rssi_query_client("ra0",&q,fake_rssi_query,&mode,&out)==1);
  assert(out.count==1&&out.records[0].sequence==1);before=out;
  q.after=1;q.session[0]=11;q.session[1]=22;
  mode=1;assert(wr_rssi_query_client("ra0",&q,fake_rssi_query,&mode,&out)==-1);assert(!memcmp(&before,&out,sizeof out));
  mode=2;assert(!wr_rssi_query_client("ra0",&q,fake_rssi_query,&mode,&out));assert(!memcmp(&before,&out,sizeof out));
  mode=3;assert(!wr_rssi_query_client("ra0",&q,fake_rssi_query,&mode,&out));assert(!memcmp(&before,&out,sizeof out));
 }
 puts("PASS RSSI client transport failure, stale session and truncated response rejection");
 {
  struct wr_rssi_query_request q={0},next={0},saved;
  struct wr_rssi_query_response r={0};unsigned int i;
  q.capacity=64;r.session[0]=1;r.sequence=100;r.count=64;
  for(i=0;i<64;i++)r.records[i].sequence=i+1;
  assert(wr_rssi_query_next_cursor(&q,&r,&next));assert(next.after==64&&next.session[0]==1);
  q=next;r.count=0;saved=next;
  assert(!wr_rssi_query_next_cursor(&q,&r,&next));assert(!memcmp(&saved,&next,sizeof next));
  r.sequence=64;assert(wr_rssi_query_next_cursor(&q,&r,&next)&&next.after==64);
  r.session[0]=2;assert(!wr_rssi_query_next_cursor(&q,&r,&next));
 }
 puts("PASS RSSI bounded-page cursor does not skip unreturned records and rejects stale sessions");
 {
  struct wr_rssi_history h,before;struct wr_rssi_query_response r={0};unsigned int i;
  wr_rssi_history_init(&h);r.session[0]=11;r.session[1]=22;r.count=1;r.sequence=3;
  r.records[0].sequence=3;r.records[0].attempt=1;r.records[0].mac[0]=2;r.records[0].stage=1;
  assert(wr_rssi_history_accept(&h,0,&r));assert(h.count==1&&h.radios[0].missing==2);
  before=h;r.records[0].stage=5;
  assert(!wr_rssi_history_accept(&h,0,&r));assert(!memcmp(&h,&before,sizeof h));
  r.records[0].stage=1;r.radio=1;r.records[0].radio=1;r.sequence=1;r.records[0].sequence=1;
  assert(wr_rssi_history_accept(&h,1,&r));assert(h.radios[0].cursor.after==3&&h.radios[1].cursor.after==1);
  wr_rssi_history_restart(&h,0);r.radio=0;r.records[0].radio=0;r.session[1]=23;
  assert(wr_rssi_history_accept(&h,0,&r));assert(h.events[0].session[1]==22&&h.events[2].session[1]==23);
  for(i=0;i<300;i++){r.sequence++;r.records[0].sequence=r.sequence;assert(wr_rssi_history_accept(&h,0,&r));}
  assert(h.count==256&&h.evicted==47&&h.radios[0].restarts==1);
 }
 puts("PASS RSSI bounded history, independent radio cursors, full sessions, gaps and eviction");
 {
  struct wr_rssi_collector c;const char *names[2]={"ra0","ra0"};int mode=0;
  wr_rssi_collector_init(&c);wr_rssi_collector_tick(&c,names,fake_rssi_query,&mode,5000);
  assert(c.history.count==2&&c.health[0].available&&c.health[1].available);
  mode=3;wr_rssi_collector_tick(&c,names,fake_rssi_query,&mode,10000);
  assert(c.history.count==2&&c.history.radios[0].cursor.after==1);
  assert(!c.health[0].available&&c.health[0].error==EPROTO);
  mode=1;wr_rssi_collector_tick(&c,names,fake_rssi_query,&mode,15000);
  assert(c.history.count==2&&c.history.radios[0].cursor.after==0&&c.history.radios[1].restarts==1);
  mode=0;wr_rssi_collector_tick(&c,names,fake_rssi_query,&mode,20000);
  assert(c.history.count==4&&c.health[0].recoveries==1&&c.health[0].last_success_ms==20000);
 }
 puts("PASS RSSI collector malformed-page retention, deferred ESTALE recovery and bounded two-radio tick");
 return 0;
}
