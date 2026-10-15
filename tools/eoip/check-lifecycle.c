#include <assert.h>
#include "lifecycle.h"
struct fixture {const char *directory;int present,owned,index,create_fail,configure_fail,remove_fail,creates,removes;unsigned mtu,master,flags;};
static int query(void *context,unsigned slot,struct wr_eoip_observation *out)
{
 struct fixture *f=context;assert(slot==0);memset(out,0,sizeof(*out));
 out->owned=f->owned;out->ifindex=f->index;out->mtu=f->mtu;out->master=f->master;out->flags=f->flags;
 return f->present;
}
static int create(void *context,const struct wr_eoip_config *config)
{
 struct fixture *f=context;struct wr_eoip_state other={.fd=-1};assert(config->slot==0);
 assert(!wr_eoip_state_lock(f->directory,&other));f->creates++;
 if(f->create_fail)return 1;
 f->present=2;f->owned=1;f->index=10;return 0;
}
static int configure(void *context,const struct wr_eoip_config *config,unsigned index,unsigned *master)
{
 struct fixture *f=context;assert(index==10);*master=2;
 if(f->configure_fail==1)return 1;
 f->mtu=config->mtu+(f->configure_fail==2);f->master=2;f->flags=1;return 0;
}
static int remove_link(void *context,unsigned slot,unsigned index)
{
 struct fixture *f=context;assert(slot==0);f->removes++;
 if(f->remove_fail||!f->owned||f->index!=(int)index)return 1;
 f->present=1;return 0;
}
static int record(const char *directory,unsigned *index)
{
 struct wr_eoip_state state={.fd=-1};int result;
 assert(wr_eoip_state_lock(directory,&state));result=wr_eoip_state_read(&state,0,index);wr_eoip_state_unlock(&state);return result;
}
int main(void)
{
 char directory[]="/tmp/wr-eoip-life-XXXXXX",path[PATH_MAX];struct wr_eoip_config config;unsigned index;
 struct fixture f={.present=1};struct wr_eoip_ops ops={.context=&f,.query=query,.create=create,.configure=configure,.remove=remove_link};
 assert(mkdtemp(directory));f.directory=directory;
 assert(wr_eoip_validate("0","1","0","0.0.0.0","10.0.0.2","7","1458","0","0","br0",&config));
 assert(wr_eoip_lifecycle_start(directory,&config,&ops)==WR_EOIP_OK);
 assert(record(directory,&index)==2&&index==10);
 assert(wr_eoip_lifecycle_start(directory,&config,&ops)==WR_EOIP_REFUSED&&f.creates==1);
 f.index=11;assert(wr_eoip_lifecycle_stop(directory,0,&ops)==WR_EOIP_REFUSED&&f.removes==0);f.index=10;
 f.remove_fail=1;assert(wr_eoip_lifecycle_stop(directory,0,&ops)==WR_EOIP_UNCONFIRMED);
 assert(record(directory,&index)==2&&index==10);f.remove_fail=0;
 assert(wr_eoip_lifecycle_stop(directory,0,&ops)==WR_EOIP_OK&&record(directory,&index)==1);
 assert(wr_eoip_lifecycle_stop(directory,0,&ops)==WR_EOIP_OK);
 f.configure_fail=2;assert(wr_eoip_lifecycle_start(directory,&config,&ops)==WR_EOIP_ROLLED_BACK);
 assert(record(directory,&index)==1);f.configure_fail=0;
 f.configure_fail=1;assert(wr_eoip_lifecycle_start(directory,&config,&ops)==WR_EOIP_ROLLED_BACK);
 assert(f.present==1&&record(directory,&index)==1);
 f.remove_fail=1;assert(wr_eoip_lifecycle_start(directory,&config,&ops)==WR_EOIP_UNCONFIRMED);
 assert(record(directory,&index)==2&&index==10);f.remove_fail=0;f.configure_fail=0;
 assert(wr_eoip_lifecycle_stop(directory,0,&ops)==WR_EOIP_OK);
 f.present=2;f.owned=0;assert(wr_eoip_lifecycle_start(directory,&config,&ops)==WR_EOIP_REFUSED);
 assert(wr_eoip_lifecycle_stop(directory,0,&ops)==WR_EOIP_REFUSED);
 f.present=1;f.create_fail=1;assert(wr_eoip_lifecycle_start(directory,&config,&ops)==WR_EOIP_UNCONFIRMED);
 assert(record(directory,&index)==1);
 snprintf(path,sizeof(path),"%s/lock",directory);unlink(path);assert(rmdir(directory)==0);
 puts("PASS EoIP lifecycle: whole-action lock, identity persistence, foreign refusal, config rollback, uncertain cleanup");return 0;
}
