#!/usr/bin/env python3
"""Extract actual client status function; injected mailbox is not OS evidence."""
import argparse
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('client',type=Path)
p.add_argument('output',type=Path)
a=p.parse_args()
source=a.client.read_text(encoding='utf-8')
anchor='int wr_iot_rc_status(const char *id,struct wr_iot_control_result *out)'
if source.count(anchor)!=1:
    raise SystemExit('Status function missing or duplicated')
start=source.index(anchor)
function=source[start:].strip()
if not function.endswith('}') or function.count('{')!=function.count('}'):
    raise SystemExit('Status function boundary changed')
a.output.write_text(r'''#include <assert.h>
#include <stdio.h>
#include <string.h>
#define WR_IOT_CONTROL_DIRECTORY "fixture"
enum {WR_IOT_RESULT_QUEUED=1,WR_IOT_RESULT_RUNNING,WR_IOT_RESULT_APPLIED,
 WR_IOT_RESULT_REJECTED,WR_IOT_RESULT_RECOVERY};
struct wr_iot_control_result {char id[33];int state;unsigned long long created,observed;};
struct wr_iot_mailbox {int open;};
static struct wr_iot_control_result stored;
static int open_calls,reads,observations,locked,fail_open,fail_read,answer,change;
static int wr_iot_control_id(const char *id){return id&&strlen(id)==32;}
static void wr_iot_mailbox_init(struct wr_iot_mailbox *m){m->open=0;}
static int wr_iot_mailbox_open(struct wr_iot_mailbox *m,const char *path,int create){
 assert(!strcmp(path,"fixture")&&!create&&!locked&&!m->open);
 if(++open_calls==fail_open)return 0;
 locked=m->open=1;return 1;
}
static void wr_iot_mailbox_close(struct wr_iot_mailbox *m){
 assert(locked&&m->open);locked=m->open=0;
}
static int wr_iot_mailbox_result(struct wr_iot_mailbox *m,struct wr_iot_control_result *out){
 assert(locked&&m->open);if(++reads==fail_read)return 0;
 *out=stored;return 1;
}
static int wr_iot_activation_result_observed(const struct wr_iot_control_result *r){
 assert(!locked&&r->state==WR_IOT_RESULT_APPLIED);observations++;
 switch(change){
 case 1:stored.id[0]='b';break;
 case 2:stored.state=WR_IOT_RESULT_QUEUED;break;
 case 3:stored.created++;break;
 case 4:stored.observed++;break;
 }
 return answer;
}
'''+function+r'''
static void reset(void){
 memset(&stored,0,sizeof(stored));memset(stored.id,'a',32);
 stored.state=WR_IOT_RESULT_APPLIED;stored.created=10;stored.observed=11;
 open_calls=reads=observations=locked=fail_open=fail_read=change=0;answer=1;
}
int main(void){
 const char *id="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
 struct wr_iot_control_result out;int i;
 reset();assert(wr_iot_rc_status(id,&out)&&out.state==WR_IOT_RESULT_APPLIED);
 assert(open_calls==2&&reads==2&&observations==1&&!locked);
 for(i=-1;i<=2;i++)if(i!=1){reset();answer=i;assert(!wr_iot_rc_status(id,&out)&&!locked);}
 for(i=1;i<=4;i++){reset();change=i;assert(!wr_iot_rc_status(id,&out)&&reads==2&&!locked);}
 for(i=1;i<=2;i++){
  reset();fail_open=i;assert(!wr_iot_rc_status(id,&out)&&!locked);
  reset();fail_read=i;assert(!wr_iot_rc_status(id,&out)&&!locked);
 }
 for(i=WR_IOT_RESULT_QUEUED;i<=WR_IOT_RESULT_RECOVERY;i++)if(i!=WR_IOT_RESULT_APPLIED){
  reset();stored.state=i;assert(wr_iot_rc_status(id,&out)&&out.state==i);
  assert(!observations&&reads==1&&!locked);
 }
 reset();stored.id[0]='b';assert(!wr_iot_rc_status(id,&out)&&!observations&&!locked);
 reset();assert(!wr_iot_rc_status(NULL,&out)&&!wr_iot_rc_status(id,NULL)&&!open_calls);
 puts("PASS actual status core: observation gate, record replacement/update, read/open failures, unlocked observer; injected mailbox only");
 return 0;
}
''',encoding='utf-8')
print('Prepared actual IoT status fixture with injected mailbox and observer')
