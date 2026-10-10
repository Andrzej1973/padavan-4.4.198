#ifndef WR_RSSI_QUERY_REQUEST_H
#define WR_RSSI_QUERY_REQUEST_H
/* Candidate wire decoder only; not installed in the driver or HTTP collector.
 * Exact 40-byte little-endian request, no native structure casting.
 * Session issuance/comparison and administrator checks belong to the handler. */
#define WR_RSSI_QUERY_REQUEST_BYTES 40
struct wr_rssi_query_request {
 unsigned long long after,session[2];
 unsigned int capacity,radio;
};
static inline unsigned long long wr_rssi_query_u64(const unsigned char *p)
{
 unsigned int i;unsigned long long v=0;
 for(i=0;i<8;i++)v|=(unsigned long long)p[i]<<(8*i);
 return v;
}
static inline int wr_rssi_query_decode(const unsigned char *p,unsigned int size,
 struct wr_rssi_query_request *out)
{
 unsigned int i;struct wr_rssi_query_request value;
 if(!p||!out||size!=WR_RSSI_QUERY_REQUEST_BYTES)return 0;
 if(p[0]!='W'||p[1]!='R'||p[2]!='S'||p[3]!='Q'||p[4]!=1||p[5])return 0;
 value.capacity=(unsigned int)p[6]|((unsigned int)p[7]<<8);
 value.radio=p[8];
 if(!value.capacity||value.capacity>64||value.radio>1)return 0;
 for(i=9;i<16;i++)if(p[i])return 0;
 value.after=wr_rssi_query_u64(p+16);
 value.session[0]=wr_rssi_query_u64(p+24);
 value.session[1]=wr_rssi_query_u64(p+32);
 /* An initial read has no session and must start at cursor zero. */
 if(value.after&&!value.session[0]&&!value.session[1])return 0;
 *out=value;return 1;
}
#endif
