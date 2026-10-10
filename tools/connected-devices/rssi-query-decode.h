#ifndef WR_RSSI_QUERY_DECODE_H
#define WR_RSSI_QUERY_DECODE_H
#include "rssi-query-request.h"
#include "rssi-query-response.h"
struct wr_rssi_query_response {
 unsigned long long session[2],sequence,overwritten;
 unsigned int count,radio;
 struct wr_rssi_record records[64];
};
/* Userspace collector parser. No output is committed until the whole bounded
 * response is validated, including its final record. */
static inline int wr_rssi_query_response_decode(const unsigned char *p,
 unsigned int size,unsigned int radio,struct wr_rssi_query_response *out)
{
 struct wr_rssi_query_response value={0};unsigned int i,j;unsigned char scratch[32];
 unsigned long long previous=0;
 if(!p||!out||radio>1||size<48||size>WR_RSSI_QUERY_RESPONSE_MAX_BYTES)return 0;
 if(p[0]!='W'||p[1]!='R'||p[2]!='S'||p[3]!='R'||p[4]!=1||p[5]||p[7])return 0;
 value.count=p[6];value.radio=p[40];
 if(value.count>64||value.radio!=radio||size!=48+value.count*32)return 0;
 for(i=41;i<48;i++)if(p[i])return 0;
 value.session[0]=wr_rssi_query_u64(p+8);value.session[1]=wr_rssi_query_u64(p+16);
 if(!value.session[0]&&!value.session[1])return 0;
 value.sequence=wr_rssi_query_u64(p+24);value.overwritten=wr_rssi_query_u64(p+32);
 for(i=0;i<value.count;i++) {
  const unsigned char *r=p+48+i*32;struct wr_rssi_record *v=&value.records[i];
  if(r[29]||r[30]||r[31])return 0;
  v->sequence=wr_rssi_query_u64(r);v->uptime_ms=wr_rssi_query_u64(r+8);
  for(j=0;j<4;j++)v->attempt|=(unsigned int)r[16+j]<<(8*j);
  for(j=0;j<6;j++)v->mac[j]=r[20+j];
  v->radio=r[26];v->bss=r[27];v->stage=r[28];
  if(v->radio!=radio||v->sequence<=previous||v->sequence>value.sequence||
     !wr_rssi_query_record_encode(scratch,32,v))return 0;
  previous=v->sequence;
 }
 *out=value;return 1;
}
#endif
