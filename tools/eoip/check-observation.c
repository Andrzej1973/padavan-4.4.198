#include <assert.h>
#include <stdio.h>
#include "observation.h"
#include "../../overlay/padavan-4.4/candidates/eoip/unified/eoip_proto.h"
_Static_assert(IFLA_EOIP_KA_INTERVAL==32&&IFLA_EOIP_KA_RETRIES==33,"EoIP observation ABI changed");
static unsigned char message[512],nested[128],parameters[64];
static size_t add(unsigned char *p,size_t at,unsigned type,const void *data,size_t n)
{
 struct rtattr h;h.rta_type=(unsigned short)type;h.rta_len=(unsigned short)RTA_LENGTH(n);
 memcpy(p+at,&h,sizeof(h));memcpy(p+at+RTA_LENGTH(0),data,n);return at+RTA_ALIGN(h.rta_len);
}
static size_t packet(const char *kind,const char *alias)
{
 struct nlmsghdr h;struct ifinfomsg info;uint32_t mtu=1458,master=2,local=0,remote=0x01020304,id=65535,interval=10;unsigned char retries=255;size_t at,n,p=0;
 memset(message,0,sizeof(message));memset(nested,0,sizeof(nested));memset(&h,0,sizeof(h));memset(&info,0,sizeof(info));
 h.nlmsg_type=RTM_NEWLINK;h.nlmsg_seq=7;info.ifi_index=10;info.ifi_flags=1;
 at=NLMSG_LENGTH(sizeof(info));memcpy(message+NLMSG_HDRLEN,&info,sizeof(info));
 at=add(message,at,IFLA_IFNAME,"wr-eoip0",9);
 at=add(message,at,IFLA_IFALIAS,alias,strlen(alias)+1);
 p=add(parameters,p,IFLA_GRE_LOCAL,&local,4);p=add(parameters,p,IFLA_GRE_REMOTE,&remote,4);
 p=add(parameters,p,IFLA_GRE_IKEY,&id,4);p=add(parameters,p,32,&interval,4);p=add(parameters,p,33,&retries,1);
 /* DATA before KIND is valid and must not be interpreted for foreign kinds. */
 n=add(nested,0,IFLA_INFO_DATA,parameters,p);n=add(nested,n,IFLA_INFO_KIND,kind,strlen(kind)+1);at=add(message,at,IFLA_LINKINFO,nested,n);
 at=add(message,at,IFLA_MTU,&mtu,sizeof(mtu));at=add(message,at,IFLA_MASTER,&master,sizeof(master));
 h.nlmsg_len=(unsigned)at;memcpy(message,&h,sizeof(h));return at;
}
int main(void)
{
 struct wr_eoip_observation out;size_t n=packet("eoip","wr-eoip:0:v1");unsigned char unaligned[513];
 assert(wr_eoip_decode_link(message,n,7,"wr-eoip0","wr-eoip:0:v1",&out));
 assert(out.owned&&out.ifindex==10&&out.flags==1&&out.mtu==1458&&out.master==2);
 assert(out.parameters==31&&out.local==0&&out.remote==0x01020304&&out.tunnel_id==65535&&out.keepalive==10&&out.retries==255);
 memcpy(unaligned+1,message,n);assert(wr_eoip_decode_link(unaligned+1,n,7,"wr-eoip0","wr-eoip:0:v1",&out));
 n=packet("bridge","wr-eoip:0:v1");assert(wr_eoip_decode_link(message,n,7,"wr-eoip0","wr-eoip:0:v1",&out)&&!out.owned);
 assert(out.parameters==0);
 n=packet("eoip","foreign");assert(wr_eoip_decode_link(message,n,7,"wr-eoip0","wr-eoip:0:v1",&out)&&!out.owned);
 assert(!wr_eoip_decode_link(message,n,8,"wr-eoip0","wr-eoip:0:v1",&out)&&!out.ifindex);
 assert(!wr_eoip_decode_link(message,n,7,"br0","wr-eoip:0:v1",&out));
 assert(!wr_eoip_decode_link(message,n-1,7,"wr-eoip0","wr-eoip:0:v1",&out));
 n=packet("eoip","wr-eoip:0:v1");n=add(message,n,IFLA_IFALIAS,"foreign",8);
 {struct nlmsghdr h;memcpy(&h,message,sizeof(h));h.nlmsg_len=(unsigned)n;memcpy(message,&h,sizeof(h));}
 assert(!wr_eoip_decode_link(message,n,7,"wr-eoip0","wr-eoip:0:v1",&out));
 n=packet("eoip","wr-eoip:0:v1");
 {struct rtattr h;memcpy(&h,message+NLMSG_LENGTH(sizeof(struct ifinfomsg)),sizeof(h));h.rta_len=2;memcpy(message+NLMSG_LENGTH(sizeof(struct ifinfomsg)),&h,sizeof(h));}
 assert(!wr_eoip_decode_link(message,n,7,"wr-eoip0","wr-eoip:0:v1",&out)&&!out.owned);
 puts("PASS EoIP observation: kind/alias ownership, flags, MTU, master, unaligned input, sequence and truncation");return 0;
}
