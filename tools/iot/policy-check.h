/* Match complete expected INPUT/FORWARD prefixes in a committed filter-table
 * snapshot. Later generic rules are harmless only after the complete IoT drops.
 * Caller builds expected rules with firewall_plan and captures live output. */
#ifndef WR_IOT_POLICY_CHECK_H
#define WR_IOT_POLICY_CHECK_H
#include "policy-normalize.h"
static inline int wr_iot_policy_line(char out[1024],const char *data,size_t size,size_t *offset){
 const char *end;size_t n;
 if(*offset>=size)return 0;
 end=memchr(data+*offset,'\n',size-*offset);if(!end)return -1;
 n=(size_t)(end-data)-*offset;if(n>=1024)return -1;
 memcpy(out,data+*offset,n);out[n]=0;*offset+=n+1;return 1;
}
static inline int wr_iot_policy_expected(char out[1024],const char *rules,size_t size,
 const char *chain,size_t index){
 char line[1024];size_t offset=0,found=0;int result;
 while((result=wr_iot_policy_line(line,rules,size,&offset))==1){
  if(!strncmp(line,chain,strlen(chain))&&found++==index)
   return wr_iot_policy_normalize(out,1024,line);
 }
 return 0;
}
static inline int wr_iot_policy_snapshot(const char *data,size_t size,const char *rules){
 char line[1024],actual[1024],expected[1024];
 size_t offset=0,length,in=0,fwd=0,expected_in=0,expected_fwd=0;
 int result,filter=0,seen=0,committed=0;
 if(!data||!size||size>256U*1024U||memchr(data,0,size)||!rules)return 0;
 length=strlen(rules);if(!length||length>8192)return 0;
 while((result=wr_iot_policy_line(line,rules,length,&offset))==1){
  if(!wr_iot_policy_normalize(expected,sizeof(expected),line))return 0;
  if(!strncmp(line,"-A INPUT ",9))expected_in++;
  else if(!strncmp(line,"-A FORWARD ",11))expected_fwd++;
  else return 0;
 }
 if(result<0||!expected_in||!expected_fwd)return 0;
 offset=0;
 while((result=wr_iot_policy_line(line,data,size,&offset))==1){
  if(!*line||line[0]=='#')continue;
  if(line[0]=='*'){
   if(filter)return 0;
   filter=!strcmp(line,"*filter");if(filter&&seen++)return 0;
   continue;
  }
  if(!strcmp(line,"COMMIT")){
   if(filter){if(in!=expected_in||fwd!=expected_fwd)return 0;filter=0;committed=1;}
   continue;
  }
  if(!filter||line[0]==':')continue;
  if(strncmp(line,"-A ",3))return 0;
  if(!strncmp(line,"-A INPUT ",9)&&in<expected_in){
   if(!wr_iot_policy_expected(expected,rules,length,"-A INPUT ",in++)||
      !wr_iot_policy_normalize(actual,sizeof(actual),line)||strcmp(actual,expected))return 0;
  }
  if(!strncmp(line,"-A FORWARD ",11)&&fwd<expected_fwd){
   if(!wr_iot_policy_expected(expected,rules,length,"-A FORWARD ",fwd++)||
      !wr_iot_policy_normalize(actual,sizeof(actual),line)||strcmp(actual,expected))return 0;
  }
 }
 return result==0&&seen==1&&committed&&!filter;
}
#endif
