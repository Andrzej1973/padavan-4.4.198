#include <assert.h>
struct wr_eoip_observation;
static int mock_query(const char *,const char *,struct wr_eoip_observation *);
#define WR_EOIP_QUERY_LINK mock_query
#define main eoip_cli_main
#include "../../overlay/padavan-4.4/candidates/eoip/eoipcr.c"
#undef main
static int initial=2,after=1,owned=1,index_value=10,fail_send,queries,sent;
static int mock_query(const char *name,const char *owner,struct wr_eoip_observation *out)
{
 assert(!strcmp(name,"wr-eoip0")&&!strcmp(owner,"wr-eoip:0:v1"));
 memset(out,0,sizeof(*out));out->owned=owned;out->ifindex=index_value;
 return queries++?after:initial;
}
int __wrap_rtnl_open(struct rtnl_handle *rth,unsigned subscriptions)
{assert(!subscriptions);rth->fd=-1;return 0;}
void __wrap_rtnl_close(struct rtnl_handle *rth){(void)rth;}
int __wrap_rtnl_talk(struct rtnl_handle *rth,struct nlmsghdr *message,pid_t peer,unsigned groups,struct nlmsghdr *answer)
{
 struct ifinfomsg info;(void)rth;assert(!peer&&!groups&&!answer);
 memcpy(&info,NLMSG_DATA(message),sizeof(info));
 assert(message->nlmsg_type==RTM_DELLINK&&info.ifi_index==10);sent++;
 return fail_send?-1:0;
}
static int run(void)
{
 char *args[]={"eoip-ctl","owned-remove","0","10",NULL};queries=0;sent=0;
 return eoip_cli_main(4,args);
}
int main(void)
{
 assert(find_cmd(cmds,"remove")==C_REMOVE);
 assert(run()==0&&sent==1&&queries==2);
 initial=1;assert(run()==0&&sent==0);initial=0;assert(run()!=0&&sent==0);initial=2;
 owned=0;assert(run()!=0&&sent==0);owned=1;
 index_value=11;assert(run()!=0&&sent==0);index_value=10;
 fail_send=1;assert(run()!=0&&sent==1&&queries==1);fail_send=0;
 after=2;assert(run()!=0&&sent==1&&queries==2);after=0;assert(run()!=0&&sent==1);after=1;
 assert(eoip_remove_owned(8,10)!=0&&eoip_remove_owned(0,0)!=0);
 puts("PASS EoIP owned remove: kind/alias ownership, expected index, absent, unknown, failure and postcheck");return 0;
}
