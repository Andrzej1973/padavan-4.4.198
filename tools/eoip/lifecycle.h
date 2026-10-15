#ifndef WR_EOIP_LIFECYCLE_H
#define WR_EOIP_LIFECYCLE_H
#include "config.h"
#include "observation.h"
#include "runtime-state.h"
/* Callbacks: query uses unknown=0/absent=1/present=2; mutations return 0 on success.
 * Adapter must independently enforce ownership for configure/remove by index. */
struct wr_eoip_ops {
 void *context;
 int (*query)(void *,unsigned,struct wr_eoip_observation *);
 int (*create)(void *,const struct wr_eoip_config *);
 int (*configure)(void *,const struct wr_eoip_config *,unsigned,unsigned *);
 int (*remove)(void *,unsigned,unsigned);
};
enum wr_eoip_action_result {WR_EOIP_OK=0,WR_EOIP_REFUSED=1,WR_EOIP_UNCONFIRMED=2,WR_EOIP_ROLLED_BACK=3};
static int wr_eoip_rollback(struct wr_eoip_state *state,unsigned slot,unsigned index,const struct wr_eoip_ops *ops)
{
 struct wr_eoip_observation observed;
 if(ops->remove(ops->context,slot,index)||ops->query(ops->context,slot,&observed)!=1||
    !wr_eoip_state_clear(state,slot,index))return WR_EOIP_UNCONFIRMED;
 return WR_EOIP_ROLLED_BACK;
}
/* Caller supplies a fully validated profile; existing links are never replaced. */
static int wr_eoip_lifecycle_start(const char *directory,const struct wr_eoip_config *config,const struct wr_eoip_ops *ops)
{
 struct wr_eoip_state state={.fd=-1};struct wr_eoip_observation observed;
 unsigned prior=0,index=0,master=0;int recorded,result=WR_EOIP_REFUSED;
 if(!config||!ops||!ops->query||!ops->create||!ops->configure||!ops->remove||
    config->slot>=WR_EOIP_SLOTS||config->enabled!=1||!wr_eoip_state_lock(directory,&state))return result;
 recorded=wr_eoip_state_read(&state,config->slot,&prior);
 if(recorded==0||ops->query(ops->context,config->slot,&observed)!=1)goto done;
 if(recorded==2&&!wr_eoip_state_clear(&state,config->slot,prior))goto done;
 /* An error acknowledgement may still leave uncertain kernel state: do not adopt. */
 if(ops->create(ops->context,config)){result=WR_EOIP_UNCONFIRMED;goto done;}
 if(ops->query(ops->context,config->slot,&observed)!=2||!observed.owned||observed.ifindex<=0){
  result=WR_EOIP_UNCONFIRMED;goto done;
 }
 index=(unsigned)observed.ifindex;
 if(!wr_eoip_state_write(&state,config->slot,index)){
  result=wr_eoip_rollback(&state,config->slot,index,ops);goto done;
 }
 if(ops->configure(ops->context,config,index,&master)||
    ops->query(ops->context,config->slot,&observed)!=2||!observed.owned||
    observed.ifindex!=(int)index||observed.mtu!=config->mtu||observed.master!=master||!(observed.flags&1U)||
    observed.parameters!=31||observed.local!=config->local.s_addr||observed.remote!=config->remote.s_addr||
    observed.tunnel_id!=config->tunnel_id||observed.keepalive!=config->keepalive||observed.retries!=config->retries){
  result=wr_eoip_rollback(&state,config->slot,index,ops);goto done;
 }
 result=WR_EOIP_OK;
 done:
 wr_eoip_state_unlock(&state);return result;
}
/* Cleanup deliberately needs no endpoint/MTU/profile validation. */
static int wr_eoip_lifecycle_stop(const char *directory,unsigned slot,const struct wr_eoip_ops *ops)
{
 struct wr_eoip_state state={.fd=-1};struct wr_eoip_observation observed;
 unsigned index=0;int recorded,present,result=WR_EOIP_REFUSED;
 if(slot>=WR_EOIP_SLOTS||!ops||!ops->query||!ops->remove||!wr_eoip_state_lock(directory,&state))return result;
 recorded=wr_eoip_state_read(&state,slot,&index);if(!recorded)goto done;
 present=ops->query(ops->context,slot,&observed);
 if(present==1){result=recorded==1||wr_eoip_state_clear(&state,slot,index)?WR_EOIP_OK:WR_EOIP_UNCONFIRMED;goto done;}
 if(present!=2||recorded!=2||!observed.owned||observed.ifindex!=(int)index)goto done;
 result=wr_eoip_rollback(&state,slot,index,ops);
 if(result==WR_EOIP_ROLLED_BACK)result=WR_EOIP_OK;
 done:
 wr_eoip_state_unlock(&state);return result;
}
#endif
