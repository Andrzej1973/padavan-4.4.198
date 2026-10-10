#ifndef WR_RSSI_QUERY_RECORD_H
#define WR_RSSI_QUERY_RECORD_H
#include "rssi-record.h"
#define WR_RSSI_QUERY_RECORD_BYTES 32
static inline void wr_rssi_query_put64(unsigned char *p,unsigned long long value)
{
 unsigned int i;for(i=0;i<8;i++)p[i]=(unsigned char)(value>>(8*i));
}
/* Encode only after the kernel snapshot lock is released. No native padding
 * or pointer values cross this boundary. Invalid input leaves output intact. */
static inline int wr_rssi_query_record_encode(unsigned char *p,unsigned int capacity,
 const struct wr_rssi_record *r)
{
 unsigned int i;unsigned char any=0;
 if(!p||!r||capacity<32||!r->sequence||!r->attempt||r->radio>1||r->bss>15||
    r->stage<WR_RSSI_DECISION||r->stage>WR_RSSI_ENTRY_CLEARED||(r->mac[0]&1))return 0;
 for(i=0;i<6;i++){any|=r->mac[i];}
 if(!any)return 0;
 wr_rssi_query_put64(p,r->sequence);wr_rssi_query_put64(p+8,r->uptime_ms);
 for(i=0;i<4;i++)p[16+i]=(unsigned char)(r->attempt>>(8*i));
 for(i=0;i<6;i++)p[20+i]=r->mac[i];
 p[26]=r->radio;p[27]=r->bss;p[28]=r->stage;
 p[29]=p[30]=p[31]=0;return 1;
}
#endif
