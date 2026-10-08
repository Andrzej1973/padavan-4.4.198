/* Candidate transformation into a temporary stream; never write a live profile. */
#ifndef WR_IOT_PROFILE_STREAM_H
#define WR_IOT_PROFILE_STREAM_H
#include "profile-line.h"
#include <stdio.h>
static int wr_iot_read_line(FILE *input,char *line,size_t capacity) {
 size_t n=0;int c;
 while((c=fgetc(input))!=EOF){
  if(c==0||n+1>=capacity)return -1;
  line[n++]=(char)c;if(c=='\n')break;
 }
 if(ferror(input))return -1;
 line[n]='\0';return n?1:0;
}
static int wr_iot_profile_stream(FILE *input,FILE *temporary,const char *ssid,const char *password,int enabled) {
 static const char *const required[]={"BssidNum","SSID1","SSID2","SSID3","WPAPSK1","WPAPSK2","WPAPSK3","AuthMode","EncrypType","WmmCapable","DLSCapable","NoForwarding","HideSSID","StationKeepAlive","PreAuth","IEEE8021X","FixedTxMode","HT_MCS"};
 unsigned char seen[sizeof(required)/sizeof(required[0])]={0};
 char line[2048],transformed[4096];const char *eq;long start;size_t i,key_size;int status;
 if(!input||!temporary||input==temporary)return 0;
 start=ftell(input);if(start<0)return 0;
 /* Entire input and all required-key multiplicities are checked before output. */
 while((status=wr_iot_read_line(input,line,sizeof(line)))>0){
  if(!wr_iot_profile_line(transformed,sizeof(transformed),line,ssid,password,enabled))return 0;
  if(enabled&&(eq=strchr(line,'='))!=NULL){
   key_size=(size_t)(eq-line);
   for(i=0;i<sizeof(required)/sizeof(required[0]);i++)if(strlen(required[i])==key_size&&!strncmp(line,required[i],key_size)){
    if(seen[i])return 0;
    seen[i]=1;break;
   }
  }
 }
 if(status<0)return 0;
 if(enabled)for(i=0;i<sizeof(seen);i++)if(!seen[i])return 0;
 if(fseek(input,start,SEEK_SET))return 0;
 while((status=wr_iot_read_line(input,line,sizeof(line)))>0){
  if(!wr_iot_profile_line(transformed,sizeof(transformed),line,ssid,password,enabled)||fputs(transformed,temporary)==EOF)return 0;
 }
 return status==0&&!ferror(temporary);
}
#endif
