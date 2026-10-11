/* Normalize only known equivalent renderings from legacy iptables-save.
 * Preserve chain, option order, negation, ports and targets for exact comparison.
 * Unsupported/oversized forms fail; this is not an installed-policy proof. */
#ifndef WR_IOT_POLICY_NORMALIZE_H
#define WR_IOT_POLICY_NORMALIZE_H
#include <arpa/inet.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static inline int wr_iot_policy_address(char out[32],const char *text){
 char copy[64],*slash,*end;struct in_addr address,netmask;
 unsigned long prefix=32;uint32_t mask=UINT32_MAX,value,inverse;
 if(strlen(text)>=sizeof(copy))return 0;
 strcpy(copy,text);slash=strchr(copy,'/');
 if(slash){
  *slash++=0;if(!*slash)return 0;
  if(strchr(slash,'.')){
   if(inet_pton(AF_INET,slash,&netmask)!=1)return 0;
   mask=ntohl(netmask.s_addr);inverse=~mask;
   if(inverse&(inverse+1U))return 0;
   prefix=0;while(prefix<32&&(mask&(UINT32_C(1)<<(31-prefix))))prefix++;
  }else{
   const char *p;for(p=slash;*p;p++)if(*p<'0'||*p>'9')return 0;
   prefix=strtoul(slash,&end,10);if(*end||prefix>32)return 0;
   mask=prefix?UINT32_MAX<<(32-prefix):0;
  }
 }
 if(inet_pton(AF_INET,copy,&address)!=1)return 0;
 value=ntohl(address.s_addr)&mask;
 return snprintf(out,32,"%u.%u.%u.%u/%lu",value>>24,(value>>16)&255,(value>>8)&255,value&255,prefix)>0;
}
static inline int wr_iot_policy_states(char out[64],const char *text){
 static const char *const names[]={"INVALID","ESTABLISHED","RELATED","NEW","UNTRACKED"};
 char copy[128],*save,*token;unsigned int bits=0;size_t i,used=0;
 if(!*text||strlen(text)>=sizeof(copy)||*text==','||text[strlen(text)-1]==','||strstr(text,",,"))return 0;
 strcpy(copy,text);
 for(token=strtok_r(copy,",",&save);token;token=strtok_r(NULL,",",&save)){
  for(i=0;i<5;i++)if(!strcmp(token,names[i]))break;
  if(i==5||(bits&(1U<<i)))return 0;
  bits|=1U<<i;
 }
 out[0]=0;
 for(i=0;i<5;i++)if(bits&(1U<<i)){
  int n=snprintf(out+used,64-used,"%s%s",used?",":"",names[i]);
  if(n<0||(size_t)n>=64-used)return 0;
  used+=(size_t)n;
 }
 return bits!=0;
}
static inline int wr_iot_policy_normalize(char *out,size_t capacity,const char *rule){
 char copy[1024],result[1024],value[64],*tokens[128],*save,*token;
 const char *protocol=NULL;size_t count=0,i,used=0;
 if(!out||!capacity||!rule||strlen(rule)>=sizeof(copy))return 0;
 strcpy(copy,rule);
 for(token=strtok_r(copy," \t\r\n",&save);token;token=strtok_r(NULL," \t\r\n",&save)){
  if(count==128)return 0;
  tokens[count++]=token;
 }
 if(count<3||strcmp(tokens[0],"-A"))return 0;
 for(i=2;i+1<count;i++)if(!strcmp(tokens[i],"-p")){
  if(protocol)return 0;
  protocol=tokens[i+1];
 }
 result[0]=0;
 for(i=0;i<count;i++){
  const char *part=tokens[i];int n;
  if(!strcmp(part,"-m")&&i+1<count&&protocol&&
     (!strcmp(protocol,"udp")||!strcmp(protocol,"tcp"))&&!strcmp(tokens[i+1],protocol)){i++;continue;}
  if(i&&(!strcmp(tokens[i-1],"-s")||!strcmp(tokens[i-1],"-d"))){
   if(!wr_iot_policy_address(value,part))return 0;
   part=value;
  }else if(i&&!strcmp(tokens[i-1],"--state")){
   if(!wr_iot_policy_states(value,part))return 0;
   part=value;
  }
  n=snprintf(result+used,sizeof(result)-used,"%s%s",used?" ":"",part);
  if(n<0||(size_t)n>=sizeof(result)-used)return 0;
  used+=(size_t)n;
 }
 if(used>=capacity)return 0;
 memcpy(out,result,used+1);return 1;
}
#endif
