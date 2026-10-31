#include <stdio.h>
#include <stdlib.h>
#define CHECK(x) do{if(!(x)){fprintf(stderr,"failed %d: %s\n",__LINE__,#x);exit(42);}}while(0)
#define FALSE 0
#define WCID_ALL 255
#define WR_IOT_WCID_APPLIED 0
#define WR_IOT_WCID_NOT_WRITTEN (-1)
typedef int INT;
typedef unsigned char UCHAR;
struct entry {int wds;};
struct adapter {int MacTabLock;};
static int locked,checked_calls,legacy_calls,software_release,hardware_result,observed,observed_result;
#define IS_ENTRY_WDS(e) ((e)->wds)
#define wr_iot_delete_wcid_checked(a,w) ((void)(a),(void)(w),checked_calls++,hardware_result)
#define RTMP_STA_ENTRY_MAC_RESET(a,w) do{(void)(a);(void)(w);legacy_calls++;}while(0)
#define NdisReleaseSpinLock(l) do{(void)(l);CHECK(locked);locked=0;}while(0)
#define wr_iot_wds_record_hardware_delete(a,p,w,r) do{(void)(a);(void)(p);(void)(w);observed++;observed_result=(r);}while(0)
static int deletion(struct adapter *pAd,struct entry *pEntry,unsigned int wcid)
{
 (void)pAd;(void)pEntry;
#include "wr-iot-wds-hardware-delete-result.inc"
 software_release++;return 1;
}
static void setup(void){locked=1;checked_calls=legacy_calls=software_release=observed=0;observed_result=99;}
int main(void)
{
 struct adapter a={0};struct entry e={1};int result;
 for(result=-2;result<=0;result++){
  setup();hardware_result=result;
#if defined(MT_MAC) && defined(WDS_SUPPORT)
  CHECK(deletion(&a,&e,1)==(result==0));
  CHECK(checked_calls==1&&!legacy_calls&&software_release==(result==0)&&locked==(result==0));
  CHECK(observed==1&&observed_result==result);
#else
  CHECK(deletion(&a,&e,1)&&legacy_calls==1&&!checked_calls&&software_release==1);
#endif
 }
 setup();e.wds=0;CHECK(deletion(&a,&e,1)&&legacy_calls==1&&!checked_calls);
 e.wds=1;
#if defined(MT_MAC) && defined(WDS_SUPPORT)
 setup();CHECK(!deletion(&a,&e,255)&&!checked_calls&&!legacy_calls&&!software_release&&!locked);
 CHECK(observed==1&&observed_result==WR_IOT_WCID_NOT_WRITTEN);
 setup();CHECK(!deletion(&a,&e,256)&&!checked_calls&&!legacy_calls&&!software_release&&!locked);
#endif
 puts("PASS WDS checked hardware deletion result propagation");return 0;
}
