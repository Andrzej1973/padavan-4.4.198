#ifndef WR_RSSI_QUERY_CLIENT_H
#define WR_RSSI_QUERY_CLIENT_H
#include <sys/socket.h>
#include <linux/wireless.h>
#include <string.h>
#include "rssi-query-cursor.h"
#define WR_RSSI_READ_IOCTL (SIOCIWFIRSTPRIV+1)
#define WR_RSSI_READ_OID 0x7e01
typedef int (*wr_rssi_ioctl_fn)(const char *,int,struct iwreq *,void *);
/* Caller supplies an internal fixed interface and synchronous ioctl wrapper.
 * Return 1 valid response, 0 invalid input/response, -1 transport failure.
 * Transport errno is preserved; failed calls never commit output/cursor. */
static inline int wr_rssi_query_client(const char *interface,
 const struct wr_rssi_query_request *query,wr_rssi_ioctl_fn invoke,void *context,
 struct wr_rssi_query_response *output)
{
 unsigned char bytes[WR_RSSI_QUERY_RESPONSE_MAX_BYTES];struct iwreq request;
 struct wr_rssi_query_response decoded;struct wr_rssi_query_request next;unsigned int i;
 if(!interface||!query||!invoke||!output)return 0;
 for(i=0;i<IFNAMSIZ&&interface[i];i++){}
 if(!i||i==IFNAMSIZ)return 0;
 memset(bytes,0,sizeof bytes);memset(&request,0,sizeof request);
 if(!wr_rssi_query_request_encode(bytes,sizeof bytes,query))return 0;
 memcpy(request.ifr_name,interface,i);
 request.u.data.pointer=bytes;request.u.data.length=sizeof bytes;request.u.data.flags=WR_RSSI_READ_OID;
 if(invoke(interface,WR_RSSI_READ_IOCTL,&request,context)<0)return -1;
 if(request.u.data.pointer!=bytes||request.u.data.flags!=WR_RSSI_READ_OID||
    !wr_rssi_query_response_decode(bytes,request.u.data.length,query->radio,&decoded)||
    decoded.count>query->capacity||decoded.sequence<query->after||
    !wr_rssi_query_session_matches(query,decoded.session))return 0;
 if(!wr_rssi_query_next_cursor(query,&decoded,&next))return 0;
 *output=decoded;return 1;
}
#endif
