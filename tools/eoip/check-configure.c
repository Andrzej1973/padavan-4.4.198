#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "configure.h"

struct mock_link {
 const char *name;
 int ifindex;
 unsigned flags,mtu,master;
 const char *kind;
 const char *alias;
};
static struct mock_link links[4];
static int link_count,talk_calls,fail_talk,apply_talk;
static unsigned last_index,last_mtu,last_master,last_flags,last_change;

static int mock_query(void *context,const char *name,const char *owner,struct wr_eoip_observation *out)
{
 int i;

 (void)context;
 for(i=0;i<link_count;i++){
  if(strcmp(links[i].name,name))continue;
  memset(out,0,sizeof(*out));
  out->ifindex=links[i].ifindex;
  out->flags=links[i].flags;
  out->mtu=links[i].mtu;
  out->master=links[i].master;
  snprintf(out->name,sizeof(out->name),"%s",links[i].name);
  snprintf(out->kind,sizeof(out->kind),"%s",links[i].kind);
  if(links[i].alias)snprintf(out->alias,sizeof(out->alias),"%s",links[i].alias);
  out->owned=!strcmp(links[i].kind,"eoip")&&links[i].alias&&!strcmp(links[i].alias,owner);
  return 2;
 }
 return 1;
}

static int mock_talk(void *context,const void *request,size_t length,uint32_t sequence)
{
 struct nlmsghdr header;
 struct ifinfomsg info;
 struct rtattr attribute;
 const unsigned char *cursor;
 size_t remaining;
 uint32_t value;

 (void)context;
 talk_calls++;
 assert(length>=NLMSG_LENGTH(sizeof(info)));
 memcpy(&header,request,sizeof(header));
 assert(header.nlmsg_len==length);
 assert(header.nlmsg_type==RTM_NEWLINK);
 assert(header.nlmsg_flags&NLM_F_REQUEST);
 assert(header.nlmsg_flags&NLM_F_ACK);
 assert(header.nlmsg_seq==sequence);
 memcpy(&info,(const unsigned char *)request+NLMSG_HDRLEN,sizeof(info));
 last_index=(unsigned)info.ifi_index;
 last_flags=info.ifi_flags;
 last_change=info.ifi_change;
 last_mtu=0;
 last_master=0;
 cursor=(const unsigned char *)request+NLMSG_LENGTH(sizeof(info));
 remaining=length-NLMSG_LENGTH(sizeof(info));
 while(remaining>=sizeof(attribute)){
  memcpy(&attribute,cursor,sizeof(attribute));
  if(attribute.rta_len<RTA_LENGTH(0)||attribute.rta_len>remaining)break;
  if((attribute.rta_type&0x3fff)==IFLA_MTU){
   assert(attribute.rta_len==RTA_LENGTH(sizeof(uint32_t)));
   memcpy(&value,cursor+RTA_LENGTH(0),sizeof(value));
   last_mtu=value;
  }else if((attribute.rta_type&0x3fff)==IFLA_MASTER){
   assert(attribute.rta_len==RTA_LENGTH(sizeof(uint32_t)));
   memcpy(&value,cursor+RTA_LENGTH(0),sizeof(value));
   last_master=value;
  }
  remaining-=RTA_ALIGN(attribute.rta_len);
  cursor+=RTA_ALIGN(attribute.rta_len);
 }
 if(apply_talk&&!fail_talk){
  links[0].mtu=last_mtu;
  links[0].flags|=IFF_UP;
  links[0].master=last_master;
 }
 return fail_talk?-1:0;
}

static int find_attribute(const unsigned char *request,size_t length,unsigned type,uint32_t *value)
{
 struct rtattr attribute;
 const unsigned char *cursor;
 size_t remaining;

 assert(length>=NLMSG_LENGTH(sizeof(struct ifinfomsg)));
 cursor=request+NLMSG_LENGTH(sizeof(struct ifinfomsg));
 remaining=length-NLMSG_LENGTH(sizeof(struct ifinfomsg));
 while(remaining>=sizeof(attribute)){
  memcpy(&attribute,cursor,sizeof(attribute));
  if(attribute.rta_len<RTA_LENGTH(0)||attribute.rta_len>remaining)return 0;
  if((attribute.rta_type&0x3fff)==type){
   if(attribute.rta_len!=RTA_LENGTH(sizeof(uint32_t)))return 0;
   memcpy(value,cursor+RTA_LENGTH(0),sizeof(*value));
   return 1;
  }
  remaining-=RTA_ALIGN(attribute.rta_len);
  cursor+=RTA_ALIGN(attribute.rta_len);
 }
 return 0;
}

int main(void)
{
 unsigned char request[WR_EOIP_CHANGE_LENGTH],reply[NLMSG_LENGTH(sizeof(struct nlmsgerr))+64];
 struct sockaddr_nl sender;
 struct nlmsghdr header;
 struct nlmsgerr error;
 struct ifinfomsg info;
 unsigned master,before;
 size_t length;
 uint32_t value;

 /* Builder: bounded, index-addressed, no implicit master attribute. */
 assert(!wr_eoip_build_change(NULL,sizeof(request),7,1400,0,1,&length));
 assert(!wr_eoip_build_change(request,sizeof(request),0,1400,0,1,&length));
 assert(!wr_eoip_build_change(request,sizeof(request),7,67,0,1,&length));
 assert(!wr_eoip_build_change(request,sizeof(request),7,WR_EOIP_MAX_MTU+1,0,1,&length));
 assert(!wr_eoip_build_change(request,40,7,1400,9,1,&length));
 assert(!wr_eoip_build_change(request,sizeof(request),7,1400,0,1,NULL));
 assert(wr_eoip_build_change(request,sizeof(request),7,1400,9,0x57454f43U,&length));
 memcpy(&header,request,sizeof(header));
 memcpy(&info,(const unsigned char *)request+NLMSG_HDRLEN,sizeof(info));
 assert(header.nlmsg_len==length&&header.nlmsg_type==RTM_NEWLINK);
 assert(header.nlmsg_flags==(NLM_F_REQUEST|NLM_F_ACK)&&header.nlmsg_seq==0x57454f43U);
 assert(info.ifi_index==7&&info.ifi_family==AF_UNSPEC);
 assert(info.ifi_flags==IFF_UP&&info.ifi_change==IFF_UP);
 assert(find_attribute(request,length,IFLA_MTU,&value)&&value==1400);
 assert(find_attribute(request,length,IFLA_MASTER,&value)&&value==9);
 assert(wr_eoip_build_change(request,sizeof(request),7,1400,0,1,&length));
 assert(!find_attribute(request,length,IFLA_MASTER,&value));

 /* Acknowledgement: only a zero-error echo of this change is accepted. */
 memset(reply,0,sizeof(reply));
 memset(&error,0,sizeof(error));
 error.msg.nlmsg_type=RTM_NEWLINK;
 error.msg.nlmsg_seq=0x57454f43U;
 memset(&header,0,sizeof(header));
 header.nlmsg_len=(unsigned)NLMSG_LENGTH(sizeof(error));
 header.nlmsg_type=NLMSG_ERROR;
 header.nlmsg_seq=0x57454f43U;
 memcpy(reply,&header,sizeof(header));
 memcpy(reply+NLMSG_HDRLEN,&error,sizeof(error));
 memset(&sender,0,sizeof(sender));
 sender.nl_family=AF_NETLINK;
 assert(wr_eoip_change_reply(reply,header.nlmsg_len,&sender,sizeof(sender),0,0x57454f43U));
 assert(!wr_eoip_change_reply(reply,header.nlmsg_len,&sender,sizeof(sender),0,0x57454f44U));
 assert(!wr_eoip_change_reply(reply,header.nlmsg_len,&sender,sizeof(sender),MSG_TRUNC,0x57454f43U));
 assert(!wr_eoip_change_reply(reply,header.nlmsg_len-1,&sender,sizeof(sender),0,0x57454f43U));
 assert(!wr_eoip_change_reply(reply,sizeof(sender),&sender,sizeof(sender),0,0x57454f43U));
 sender.nl_pid=1;
 assert(!wr_eoip_change_reply(reply,header.nlmsg_len,&sender,sizeof(sender),0,0x57454f43U));
 sender.nl_pid=0;
 error.error=-EPERM;
 memcpy(reply+NLMSG_HDRLEN,&error,sizeof(error));
 assert(!wr_eoip_change_reply(reply,header.nlmsg_len,&sender,sizeof(sender),0,0x57454f43U));
 error.error=0;
 error.msg.nlmsg_type=RTM_DELLINK;
 memcpy(reply+NLMSG_HDRLEN,&error,sizeof(error));
 assert(!wr_eoip_change_reply(reply,header.nlmsg_len,&sender,sizeof(sender),0,0x57454f43U));

 /* Configure: an already requested state sends nothing. */
 links[0]=(struct mock_link){"wr-eoip0",7,IFF_UP,1400,0,"eoip","wr-eoip:0:v1"};
 links[1]=(struct mock_link){"br0",9,IFF_UP,1500,0,"bridge",NULL};
 link_count=2;
 talk_calls=0;
 fail_talk=0;
 apply_talk=1;
 master=99;
 assert(wr_eoip_configure(mock_talk,NULL,mock_query,NULL,"wr-eoip0","wr-eoip:0:v1",7,1400,"",&master));
 assert(master==0&&talk_calls==0);

 /* A changed MTU is applied and then observed. */
 links[0].mtu=1300;
 master=99;
 assert(wr_eoip_configure(mock_talk,NULL,mock_query,NULL,"wr-eoip0","wr-eoip:0:v1",7,1400,"",&master));
 assert(talk_calls==1&&master==0);
 assert(last_index==7&&last_mtu==1400&&last_master==0);
 assert(last_flags==IFF_UP&&last_change==IFF_UP);
 assert(links[0].mtu==1400);

 /* An explicit bridge is verified as a bridge and attached by index. */
 master=99;
 assert(wr_eoip_configure(mock_talk,NULL,mock_query,NULL,"wr-eoip0","wr-eoip:0:v1",7,1400,"br0",&master));
 assert(master==9&&last_master==9&&links[0].master==9);

 /* An existing master is never detached implicitly. */
 assert(!wr_eoip_configure(mock_talk,NULL,mock_query,NULL,"wr-eoip0","wr-eoip:0:v1",7,1400,"",&master));
 assert(master==0);

 /* Foreign interfaces, index mismatches, absent or renamed interfaces refuse. */
 links[2]=(struct mock_link){"wr-eoip1",8,IFF_UP,1400,0,"veth","wr-eoip:1:v1"};
 link_count=3;
 assert(!wr_eoip_configure(mock_talk,NULL,mock_query,NULL,"wr-eoip1","wr-eoip:1:v1",8,1400,"",&master));
 assert(!wr_eoip_configure(mock_talk,NULL,mock_query,NULL,"wr-eoip0","wr-eoip:0:v1",8,1400,"",&master));
 assert(!wr_eoip_configure(mock_talk,NULL,mock_query,NULL,"wr-eoip0","wr-eoip:1:v1",7,1400,"",&master));
 assert(!wr_eoip_configure(mock_talk,NULL,mock_query,NULL,"wr-eoip9","wr-eoip:0:v1",7,1400,"",&master));

 /* A bridge candidate must exist, be a bridge, and not be the interface itself. */
 links[3]=(struct mock_link){"br9",10,IFF_UP,1500,0,"veth",NULL};
 link_count=4;
 assert(!wr_eoip_configure(mock_talk,NULL,mock_query,NULL,"wr-eoip0","wr-eoip:0:v1",7,1400,"br9",&master));
 assert(!wr_eoip_configure(mock_talk,NULL,mock_query,NULL,"wr-eoip0","wr-eoip:0:v1",7,1400,"wr-eoip0",&master));
 assert(!wr_eoip_configure(mock_talk,NULL,mock_query,NULL,"wr-eoip0","wr-eoip:0:v1",7,1400,"br7",&master));
 assert(master==0);

 /* Transport failure and an unconfirmed post-state refuse after the change. */
 links[0].master=0;
 links[0].mtu=1300;
 link_count=2;
 fail_talk=1;
 assert(!wr_eoip_configure(mock_talk,NULL,mock_query,NULL,"wr-eoip0","wr-eoip:0:v1",7,1400,"",&master));
 fail_talk=0;
 apply_talk=0;
 assert(!wr_eoip_configure(mock_talk,NULL,mock_query,NULL,"wr-eoip0","wr-eoip:0:v1",7,1400,"",&master));
 apply_talk=1;
 assert(master==0);

 /* Malformed requests never reach the transport. */
 before=(unsigned)talk_calls;
 assert(!wr_eoip_configure(mock_talk,NULL,mock_query,NULL,"wr-eoip0","wr-eoip:0:v1",0,1400,"",&master));
 assert(!wr_eoip_configure(mock_talk,NULL,mock_query,NULL,"wr-eoip0","wr-eoip:0:v1",7,67,"",&master));
 assert(!wr_eoip_configure(mock_talk,NULL,mock_query,NULL,"wr-eoip0","",7,1400,"",&master));
 assert(!wr_eoip_configure(mock_talk,NULL,mock_query,NULL,"bad name!","wr-eoip:0:v1",7,1400,"",&master));
 assert(!wr_eoip_configure(mock_talk,NULL,mock_query,NULL,"wr-eoip0","wr-eoip:0:v1",7,1400,NULL,&master));
 assert(!wr_eoip_configure(NULL,NULL,mock_query,NULL,"wr-eoip0","wr-eoip:0:v1",7,1400,"",&master));
 assert(!wr_eoip_configure(mock_talk,NULL,NULL,NULL,"wr-eoip0","wr-eoip:0:v1",7,1400,"",&master));
 assert(!wr_eoip_configure(mock_talk,NULL,mock_query,NULL,"wr-eoip0","wr-eoip:0:v1",7,1400,"",NULL));
 assert((unsigned)talk_calls==before);

 /* The real transport rejects an unknown index and a truncated request. */
 assert(wr_eoip_build_change(request,sizeof(request),1000000U,1400,0,0x57454f43U,&length));
 assert(wr_eoip_socket_change(NULL,request,length,0x57454f43U)!=0);
 assert(wr_eoip_socket_change(NULL,NULL,0,0x57454f43U)!=0);

 puts("PASS EoIP configure: ownership/index precheck, explicit bridge verification, no implicit detach, verified change");
 return 0;
}