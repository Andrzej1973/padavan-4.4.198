#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
typedef int NDIS_STATUS;
typedef unsigned int NDIS_OID;
typedef void *PVOID;
typedef unsigned int UINT32;
typedef unsigned long ULONG;
typedef unsigned char *PUCHAR;
typedef int BOOLEAN;
typedef struct cmd {void *buffer;UINT32 bufferlength;NDIS_OID command;int CmdFromNdis;} CmdQElmt,*PCmdQElmt;
typedef struct adapter {unsigned int flags;int CmdQLock,cmdQTask;struct {int CmdQState;} CmdQ;} *PRTMP_ADAPTER;
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
#define NDIS_STATUS_RESOURCES 2
#define FALSE 0
#define TRUE 1
#define fRTMP_ADAPTER_NIC_NOT_EXIST 1
#define RTMP_TASK_CAN_DO_INSERT 1
#define RTMP_TEST_FLAG(ad,flag) ((ad)->flags&(flag))
#define DBGPRINT(level,args) ((void)0)
#define NdisZeroMemory memset_zero
#define NdisMoveMemory memcpy
static int allocations,frees,fail_at,held,queued,wakes;
static PCmdQElmt owned;
static void memset_zero(void *p,size_t n){memset(p,0,n);}
static int os_alloc_mem(PRTMP_ADAPTER ad,PUCHAR *p,size_t n){
 void *allocated;
 (void)ad;allocations++;allocated=allocations==fail_at?NULL:malloc(n);
 memcpy(p,&allocated,sizeof(allocated));
 return allocated?0:2;
}
static void os_free_mem(PRTMP_ADAPTER ad,void *p){(void)ad;assert(p);free(p);frees++;}
#define RTMP_SPIN_LOCK_IRQSAVE(lock,flag) ((void)(lock),(void)(flag),assert(!held),held=1)
#define RTMP_SPIN_UNLOCK_IRQRESTORE(lock,flag) ((void)(lock),(void)(flag),assert(held),held=0)
#define EnqueueCmd(queue,cmd) ((void)(queue),assert(held&&!owned),owned=(cmd),queued++)
#define RTCMDUp(task) ((void)(task),assert(!held),wakes++)
