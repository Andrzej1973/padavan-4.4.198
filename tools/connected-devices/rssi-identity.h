#ifndef WR_RSSI_IDENTITY_H
#define WR_RSSI_IDENTITY_H
/* Caller holds station-table lock. Birth counter belongs to one adapter
 * lifetime; an adapter session is additionally required across restarts. */
struct wr_rssi_identity {
 unsigned long long birth;
 unsigned int wcid;
 unsigned char mac[6];
};
static inline int wr_rssi_identity_create(unsigned long long *counter,
 unsigned int wcid,const unsigned char *mac,struct wr_rssi_identity *out)
{
 unsigned int i;unsigned char any=0;
 if(!counter||!mac||!out||wcid>65535||*counter==~0ULL||(mac[0]&1))return 0;
 for(i=0;i<6;i++)any|=mac[i];
 if(!any)return 0;
 out->birth=++*counter;out->wcid=wcid;
 for(i=0;i<6;i++)out->mac[i]=mac[i];
 return 1;
}
static inline int wr_rssi_identity_matches(const struct wr_rssi_identity *a,
 const struct wr_rssi_identity *b)
{
 unsigned int i;
 if(!a||!b||!a->birth||a->birth!=b->birth||a->wcid!=b->wcid)return 0;
 for(i=0;i<6;i++)if(a->mac[i]!=b->mac[i])return 0;
 return 1;
}
#endif
