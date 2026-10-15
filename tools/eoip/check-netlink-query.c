#include <assert.h>
#include <stdio.h>
#include <net/if.h>
#include "netlink-query.h"
int main(void)
{
 struct wr_eoip_observation out;struct sockaddr_nl sender;
 struct {struct nlmsghdr header;struct nlmsgerr error;} reply;
 char missing[16];unsigned counter=0;
 memset(&reply,0,sizeof(reply));memset(&sender,0,sizeof(sender));sender.nl_family=AF_NETLINK;
 reply.header.nlmsg_len=sizeof(reply);reply.header.nlmsg_type=NLMSG_ERROR;reply.header.nlmsg_seq=7;
 reply.error.error=-ENODEV;reply.error.msg.nlmsg_type=RTM_GETLINK;reply.error.msg.nlmsg_seq=7;
 assert(wr_eoip_link_reply(&reply,sizeof(reply),&sender,sizeof(sender),0,7,"wr-eoip0","owner",&out)==1);
 sender.nl_pid=123;
 assert(wr_eoip_link_reply(&reply,sizeof(reply),&sender,sizeof(sender),0,7,"wr-eoip0","owner",&out)==0);
 sender.nl_pid=0;
 assert(wr_eoip_link_reply(&reply,sizeof(reply),&sender,sizeof(sender),MSG_TRUNC,7,"wr-eoip0","owner",&out)==0);
 assert(wr_eoip_link_reply(&reply,sizeof(reply),&sender,sizeof(sender)-1,0,7,"wr-eoip0","owner",&out)==0);
 reply.error.error=-EPERM;
 assert(wr_eoip_link_reply(&reply,sizeof(reply),&sender,sizeof(sender),0,7,"wr-eoip0","owner",&out)==0);
 assert(wr_eoip_query_link("../lo","owner",&out)==0);
 assert(wr_eoip_query_link("lo","owner",&out)==2);
 assert(out.ifindex>0&&!out.owned&&out.mtu>0&&!strcmp(out.name,"lo"));
 do{snprintf(missing,sizeof(missing),"wre%u",counter++);}while(if_nametoindex(missing));
 assert(wr_eoip_query_link(missing,"owner",&out)==1&&!out.ifindex);
 puts("PASS EoIP netlink: sender/truncation/error guards, real read-only loopback and missing-link queries");return 0;
}
