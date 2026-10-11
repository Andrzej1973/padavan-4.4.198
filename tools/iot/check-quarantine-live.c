#include "quarantine-live.h"
#include "quarantine.h"
#include "service-guard.h"
int main(int argc,char **argv){
 if(argc!=2)return 2;
 if(!strcmp(argv[1],"owned")||!strcmp(argv[1],"can-apply")){
  int token=wr_iot_service_guard_enter(1),ready;
  if(token!=1)return 1;
  ready=!strcmp(argv[1],"can-apply")?wr_iot_quarantine_can_apply():wr_iot_quarantine_ready();
  wr_iot_service_guard_leave(token);return ready?0:1;
 }
 if(!strcmp(argv[1],"unguarded"))return wr_iot_quarantine_ready()?0:1;
 if(!strcmp(argv[1],"4"))return wr_iot_quarantine_live(0)?0:1;
 if(!strcmp(argv[1],"6"))return wr_iot_quarantine_live(1)?0:1;
 return 2;
}
