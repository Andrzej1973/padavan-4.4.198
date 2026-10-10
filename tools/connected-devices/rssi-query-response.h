#ifndef WR_RSSI_QUERY_RESPONSE_H
#define WR_RSSI_QUERY_RESPONSE_H
#include "rssi-query-record.h"
#define WR_RSSI_QUERY_RESPONSE_HEADER_BYTES 48
#define WR_RSSI_QUERY_RESPONSE_MAX_BYTES (48+64*32)
/* Kernel snapshots are copied before entering this encoder. */
static inline unsigned int wr_rssi_query_response_encode(unsigned char *p,
 unsigned int capacity,const unsigned long long *session,
 unsigned long long sequence,unsigned long long overwritten,unsigned int radio,
 const struct wr_rssi_record *records,unsigned int count)
{
 unsigned int i,size;unsigned char scratch[32];unsigned long long previous=0;
 if(!p||!session||(!session[0]&&!session[1])||radio>1||count>64||
    (count&&!records))return 0;
 size=48+count*32;if(capacity<size)return 0;
 /* Validate the complete response before modifying the caller's buffer. */
 for(i=0;i<count;i++) {
  if(records[i].radio!=radio||records[i].sequence<=previous||records[i].sequence>sequence||
     !wr_rssi_query_record_encode(scratch,32,&records[i]))return 0;
  previous=records[i].sequence;
 }
 p[0]='W';p[1]='R';p[2]='S';p[3]='R';p[4]=1;p[5]=0;
 p[6]=(unsigned char)count;p[7]=0;
 wr_rssi_query_put64(p+8,session[0]);wr_rssi_query_put64(p+16,session[1]);
 wr_rssi_query_put64(p+24,sequence);wr_rssi_query_put64(p+32,overwritten);
 p[40]=(unsigned char)radio;for(i=41;i<48;i++)p[i]=0;
 for(i=0;i<count;i++)wr_rssi_query_record_encode(p+48+i*32,32,&records[i]);
 return size;
}
#endif
