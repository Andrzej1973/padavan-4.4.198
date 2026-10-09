/* Bounded passive networkmap reader. Caller owns the source lock/snapshot.
 * The stale flag is evidence from networkmap, not proof of current connectivity. */
#ifndef WR_DEVICE_NETWORKMAP_H
#define WR_DEVICE_NETWORKMAP_H
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <arpa/inet.h>
#define WR_DEVICE_LIMIT 128
struct wr_device_record {char ip[16],mac[18],name[129];unsigned int legacy_type;int http,networkmap_stale;};
struct wr_device_snapshot {struct wr_device_record records[WR_DEVICE_LIMIT];unsigned int count,invalid;int truncated;};
static inline int wr_device_number(const char *s,unsigned int max,unsigned int *out){
 unsigned long n=0;if(!s||!*s)return 0;
 while(*s){if(*s<'0'||*s>'9')return 0;n=n*10+(unsigned int)(*s++-'0');if(n>max)return 0;}
 *out=(unsigned int)n;return 1;
}
static inline int wr_device_hex(char c){return (c>='0'&&c<='9')||(c>='a'&&c<='f')||(c>='A'&&c<='F');}
static inline int wr_device_networkmap_record(char *line,struct wr_device_record *out){
 char *first,*second,*tail[3],*p;struct in_addr address;struct wr_device_record result;unsigned int type,http,stale;size_t n;int i;
 if(!line||!out)return 0;
 n=strlen(line);if(!n||line[n-1]!='\n')return 0;line[--n]=0;if(n&&line[n-1]=='\r')line[--n]=0;
 first=strchr(line,',');if(!first)return 0;*first++=0;second=strchr(first,',');if(!second)return 0;*second++=0;
 p=second;for(i=2;i>=0;i--){tail[i]=strrchr(p,',');if(!tail[i])return 0;*tail[i]++=0;}
 if(strlen(line)>=sizeof(result.ip)||inet_pton(AF_INET,line,&address)!=1||strlen(first)!=17)return 0;
 for(i=0;i<17;i++){if(i%3==2){if(first[i]!=':')return 0;}else if(!wr_device_hex(first[i]))return 0;}
 if(!wr_device_number(tail[0],255,&type)||!wr_device_number(tail[1],1,&http)||!wr_device_number(tail[2],1,&stale))return 0;
 memset(&result,0,sizeof(result));strcpy(result.ip,line);strcpy(result.mac,first);
 for(i=0;i<17;i++)if(result.mac[i]>='a'&&result.mac[i]<='f')result.mac[i]=(char)(result.mac[i]-'a'+'A');
 n=strlen(second);if(n>128)n=128;memcpy(result.name,second,n);
 result.legacy_type=type;result.http=(int)http;result.networkmap_stale=(int)stale;*out=result;return 1;
}
static inline int wr_device_networkmap_read(FILE *fp,struct wr_device_snapshot *out){
 char line[512];size_t bytes=0;struct wr_device_record record;
 if(!fp||!out)return 0;
 memset(out,0,sizeof(*out));
 while(fgets(line,sizeof(line),fp)){
  size_t n=strlen(line);bytes+=n;
  if(bytes>65536){out->truncated=1;break;}
  if(!n||line[n-1]!='\n'){
   int c;out->invalid++;
   while((c=fgetc(fp))!=EOF){if(++bytes>65536){out->truncated=1;break;}if(c=='\n')break;}
   if(out->truncated)break;
   continue;
  }
  if(!wr_device_networkmap_record(line,&record)){out->invalid++;continue;}
  if(out->count==WR_DEVICE_LIMIT){out->truncated=1;continue;}
  out->records[out->count++]=record;
 }
 return !ferror(fp);
}
#endif
