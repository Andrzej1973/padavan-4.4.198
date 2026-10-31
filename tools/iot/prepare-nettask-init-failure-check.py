#!/usr/bin/env python3
"""Extend extracted Init/Exit host fixture with every OS_ABL allocation failure."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('fixture',type=Path);p.add_argument('output',type=Path)
p.add_argument('--caller-source',type=Path,help='candidate common/rtmp_init_inf.c; extract actual init call and err2 tail')
a=p.parse_args()
if a.output.exists():p.error('new output required')
s=a.fixture.read_text()
start=s.index('#define RTMP_OS_TASKLET_INIT(ad,task,func,data)')
end=s.index('\n',start)
s=s[:start]+'''static int fail_at,attempts;
static int fake_init_checked(RTMP_NET_TASK_STRUCT *task){
 assert(!held&&current->wr_iot_nettask_initializing);
 attempts++;if(fail_at==attempts)return 0;
 task->initialized=1;task->killed=0;initializations++;return 1;
}
#define RTMP_OS_TASKLET_INIT(ad,task,func,data) fake_init_checked(task)'''+s[end:]
s=s.replace('int before;','int before,total,i;',1)
anchor='before=initializations;assert(RtmpNetTaskInit(&a)==1'
if s.count(anchor)!=1:p.error('changed fixture')
s=s.replace(anchor,'total=initializations;'+anchor,1)
anchor=' assert(!held);return 0;}'
if s.count(anchor)!=1:p.error('changed fixture tail')
s=s.replace(anchor,''' for(i=1;i<=total;i++){
 memset(&a,0,sizeof a);memset(&cookie,0,sizeof cookie);
 a.OS_Cookie=&cookie;current=&a;
 wr_iot_tasklet_schedule_init(&a.wr_iot_nettask_owner);a.wr_iot_nettask_joined=1;
 initializations=0;kills=0;attempts=0;fail_at=i;
 assert(RtmpNetTaskInit(&a)==1);
 assert(attempts==i&&initializations==i-1&&kills==i-1);
 assert(!a.wr_iot_nettask_initializing&&a.wr_iot_nettask_joined);
 assert(a.wr_iot_nettask_owner.blocked&&!a.wr_iot_nettask_owner.inflight);
 before=kills;assert(RtmpNetTaskExit(&a)==0&&kills==before);
 fail_at=0;attempts=0;
 assert(RtmpNetTaskInit(&a)==0&&!a.wr_iot_nettask_initializing);
 assert(RtmpNetTaskExit(&a)==0&&kills==initializations);
 }
 assert(!held);return 0;}''')
if a.caller_source:
 source=a.caller_source.read_text()
 begin=source.index('Status = RtmpNetTaskInit(pAd);')
 finish=source.index('goto err2;',begin)+len('goto err2;')
 tail_begin=source.index('\nerr2:')
 tail_end=source.index('\n}',tail_begin)
 tail=source[tail_begin:tail_end]
 if 'RtmpNetTaskExit(pAd) != NDIS_STATUS_SUCCESS' not in tail or 'hif_sys_exit(pAd)' not in tail:
  p.error('changed caller unwind')
 # Earlier goto sites are outside this extraction; preserve fallthrough code.
 tail=tail.replace('\nerr1:', '').replace('\nerr0:', '')
 helper='''
#define TRUE 1
#define FALSE 0
#define RT_DEBUG_ERROR 0
#define DBGPRINT(level,args) do{(void)(level);}while(0)
static int hif_exits;
static void hif_sys_exit(RTMP_ADAPTER *ad){
 assert(ad->wr_iot_nettask_joined&&!ad->wr_iot_nettask_initializing);
 assert(ad->wr_iot_nettask_owner.blocked);hif_exits++;
}
static int actual_init_caller_tail(RTMP_ADAPTER *pAd){int Status;
'''+source[begin:finish]+'\nreturn TRUE;'+tail+'\n}\n'
 s=s.replace('int main(void)',helper+'int main(void)',1)
 s=s.replace('assert(RtmpNetTaskInit(&a)==1);',
  'hif_exits=0;assert(actual_init_caller_tail(&a)==0&&hif_exits==1);',1)
a.output.write_text(s,encoding='utf-8')
print('Injected each enabled OS_ABL allocation failure, partial cleanup and successful retry')
