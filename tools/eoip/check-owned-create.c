#include <assert.h>
#define main eoip_cli_main
#include "../../overlay/padavan-4.4/candidates/eoip/eoipcr.c"
#undef main
static unsigned sent;static int fail_send;
int __wrap_rtnl_open(struct rtnl_handle *rth,unsigned subscriptions)
{assert(!subscriptions);rth->fd=-1;return 0;}
void __wrap_rtnl_close(struct rtnl_handle *rth){(void)rth;}
int __wrap_rtnl_talk(struct rtnl_handle *rth,struct nlmsghdr *message,pid_t peer,unsigned groups,struct nlmsghdr *answer)
{
 struct ifinfomsg *info=NLMSG_DATA(message);struct rtattr *attrs[IFLA_MAX+1],*nested[IFLA_INFO_MAX+1];
 (void)rth;assert(!peer&&!groups&&!answer);sent++;
 assert(message->nlmsg_type==RTM_NEWLINK&&(message->nlmsg_flags&NLM_F_EXCL));
 parse_rtattr(attrs,IFLA_MAX,IFLA_RTA(info),(int)message->nlmsg_len-NLMSG_LENGTH(sizeof(*info)));
 assert(attrs[IFLA_IFNAME]&&attrs[IFLA_IFALIAS]&&attrs[IFLA_LINKINFO]);
 assert(RTA_PAYLOAD(attrs[IFLA_IFNAME])==9&&!strcmp(RTA_DATA(attrs[IFLA_IFNAME]),"wr-eoip0"));
 assert(RTA_PAYLOAD(attrs[IFLA_IFALIAS])==13&&!strcmp(RTA_DATA(attrs[IFLA_IFALIAS]),"wr-eoip:0:v1"));
 parse_rtattr_nested(nested,IFLA_INFO_MAX,attrs[IFLA_LINKINFO]);
 assert(nested[IFLA_INFO_KIND]&&RTA_PAYLOAD(nested[IFLA_INFO_KIND])==5&&!strcmp(RTA_DATA(nested[IFLA_INFO_KIND]),"eoip"));
 return fail_send?-1:0;
}
int main(void)
{
 char *args[]={"eoip-ctl","add","name","wr-eoip0","tunnel-id","7","remote","10.0.0.2","owner","wr-eoip:0:v1",NULL};
 assert(eoip_cli_main(10,args)==0&&sent==1);
 fail_send=1;assert(eoip_cli_main(10,args)!=0&&sent==2);fail_send=0;
 args[1]="set";assert(eoip_cli_main(10,args)!=0&&sent==2);args[1]="add";
 args[3]="br0";assert(eoip_cli_main(10,args)!=0&&sent==2);args[3]="wr-eoip0";
 args[9]="wr-eoip:1:v1";assert(eoip_cli_main(10,args)!=0&&sent==2);
 args[9]="wr-eoip:8:v1";assert(eoip_cli_main(10,args)!=0&&sent==2);
 args[9]="wr-eoip:0:v1";args[7]="::1";assert(eoip_cli_main(10,args)!=0&&sent==2);
 puts("PASS EoIP owned create: atomic alias/kind/name, exclusive flag, failures and managed-owner restrictions");return 0;
}
