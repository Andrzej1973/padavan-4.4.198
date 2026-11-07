#!/usr/bin/env python3
"""Extract real timer init/set/mod/fence admission; synchronization is injected."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new output required')
s=(a.candidate/'common/rtmp_init.c').read_text()
def extract(name):
    anchor='VOID '+name+'(';start=s.index(anchor);brace=s.index('{',start);depth=0
    for end in range(brace,len(s)):
        if s[end]=='{':depth+=1
        elif s[end]=='}':
            depth-=1
            if not depth:return s[start:end+1]
    raise ValueError(name)
prefix=r'''
#include <assert.h>
#include <stddef.h>
#include <stdint.h>
#define IN
#define TRUE 1
#define FALSE 0
#define RT_DEBUG_INFO 0
#define fRTMP_ADAPTER_HALT_IN_PROGRESS 1
#define fRTMP_ADAPTER_NIC_NOT_EXIST 2
#define DBGPRINT(l,args) do{(void)(l);}while(0)
#define DBGPRINT_ERR(args) do{}while(0)
typedef void VOID;typedef void *PVOID;typedef int BOOLEAN;typedef uintptr_t ULONG;
typedef struct {int RscTimerMemList;} RTMP_ADAPTER;
typedef struct {int TimerObj,Valid,wr_iot_retiring,PeriodicType,State,Repeat;ULONG TimerValue,cookie;void *pAd;} RALINK_TIMER_STRUCT;
static int TimerSemLock,held,arms,mods,periodic,created,listed,cancels,inject_fence,halted;
static RALINK_TIMER_STRUCT *active;
#define RTMP_SEM_LOCK(l) do{(void)(l);assert(!held);held=1;}while(0)
#define RTMP_SEM_UNLOCK(l) do{(void)(l);assert(held);held=0;}while(0)
#define WRITE_ONCE(x,v) ((x)=(v))
#define RTMP_TEST_FLAG(a,f) ((void)(a),(void)(f),halted)
#define RTMP_TimerListAdd(a,t) do{(void)(a);(void)(t);assert(held);listed++;}while(0)
#define RTMP_OS_Init_Timer(a,o,f,d,l) do{(void)(a);(void)(o);(void)(f);(void)(d);(void)(l);assert(held);created++;}while(0)
#define RTMP_OS_Add_Timer(o,v) do{(void)(o);(void)(v);assert(held&&!active->wr_iot_retiring);arms++;}while(0)
#define RTMP_OS_Mod_Timer(o,v) do{(void)(o);(void)(v);assert(held&&!active->wr_iot_retiring);mods++;}while(0)
#define RTMP_SetPeriodicTimer(o,v) do{(void)(o);(void)(v);assert(held&&!active->wr_iot_retiring);periodic++;}while(0)
'''
cancel=r'''
static void RTMPCancelTimer(RALINK_TIMER_STRUCT *t,BOOLEAN *cancelled){
 assert(!held);cancels++;*cancelled=1;if(inject_fence)wr_iot_timer_fence(t);
}
'''
suffix=r'''
int main(void){RTMP_ADAPTER a={0};RALINK_TIMER_STRUCT t={0};active=&t;
RTMPInitTimer(&a,&t,NULL,NULL,FALSE);assert(t.Valid&&!t.wr_iot_retiring&&created==1&&listed==1&&!arms);
RTMPSetTimer(&t,10);assert(arms==1&&!held);
RTMPModTimer(&t,20);assert(mods==1&&!held);
wr_iot_timer_fence(&t);assert(t.Valid&&t.wr_iot_retiring&&!t.Repeat&&t.State&&!held);
RTMPSetTimer(&t,30);RTMPModTimer(&t,30);RTMPInitTimer(&a,&t,NULL,NULL,TRUE);
assert(arms==1&&mods==1&&created==1&&listed==1&&t.wr_iot_retiring&&!held);
t=(RALINK_TIMER_STRUCT){0};RTMPInitTimer(&a,&t,NULL,NULL,TRUE);
RTMPSetTimer(&t,10);assert(periodic==1);inject_fence=1;
RTMPModTimer(&t,20);assert(cancels==1&&periodic==1&&t.wr_iot_retiring&&!held);
t=(RALINK_TIMER_STRUCT){0};wr_iot_timer_fence(&t);assert(!t.wr_iot_retiring&&!held);
wr_iot_timer_fence(NULL);return 0;}
'''
a.output.write_text(prefix+extract('RTMPInitTimer')+'\n'+extract('wr_iot_timer_fence')+'\n'+cancel+
                    extract('RTMPSetTimer')+'\n'+extract('RTMPModTimer')+'\n'+suffix,encoding='utf-8')
print('Extracted timer scheduling fence; callbacks/OS scheduling not synchronized by this test')
