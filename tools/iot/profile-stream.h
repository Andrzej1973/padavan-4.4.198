/* Candidate transformation into a temporary stream; never write a live profile. */
#ifndef WR_IOT_PROFILE_STREAM_H
#define WR_IOT_PROFILE_STREAM_H
#include "profile-scan.h"
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
static int wr_iot_profile_stream_direction(FILE *input,FILE *temporary,const char *ssid,const char *password,int enabled,int removing) {
 struct wr_iot_profile_scan scan={{0}};
 char line[2048],transformed[4096];long start;int status;
 if(!input||!temporary||input==temporary)return 0;
 start=ftell(input);if(start<0)return 0;
 /* Entire input and all required-key multiplicities are checked before output. */
 while((status=wr_iot_read_line(input,line,sizeof(line)))>0){
  if(!wr_iot_profile_scan_line(&scan,line,ssid,password,enabled,removing))return 0;
 }
 if(status<0)return 0;
 if(!wr_iot_profile_scan_complete(&scan,enabled))return 0;
 if(fseek(input,start,SEEK_SET))return 0;
 while((status=wr_iot_read_line(input,line,sizeof(line)))>0){
  if(!wr_iot_profile_line_direction(transformed,sizeof(transformed),line,ssid,password,enabled,removing)||fputs(transformed,temporary)==EOF)return 0;
 }
 return status==0&&!ferror(temporary);
}
static inline int wr_iot_profile_stream(FILE *input,FILE *temporary,const char *ssid,const char *password,int enabled){
 return wr_iot_profile_stream_direction(input,temporary,ssid,password,enabled,0);
}
/* Remove only the exact owned third-BSS fields; preserve current first two
 * entries and all unrelated radio settings. Never call the global generator. */
static inline int wr_iot_profile_disable_stream(FILE *input,FILE *temporary,const char *ssid,const char *password){
 return wr_iot_profile_stream_direction(input,temporary,ssid,password,1,1);
}
#endif
