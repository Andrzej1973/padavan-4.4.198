/* Read the effective DNS port from bounded regular config files.
 * Unsupported include-directory syntax fails explicitly rather than probing a guessed port. */
#ifndef WR_IOT_DNS_CONFIG_H
#define WR_IOT_DNS_CONFIG_H
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
struct wr_iot_dns_config_budget {unsigned int files;size_t bytes;};
static inline char *wr_iot_dns_trim(char *value){
 char *end;while(isspace((unsigned char)*value))value++;
 end=value+strlen(value);while(end>value&&isspace((unsigned char)end[-1]))*--end=0;
 return value;
}
static inline int wr_iot_dns_config_read(const char *path,unsigned int depth,struct wr_iot_dns_config_budget *budget,unsigned int *port){
 int fd,ok=1;struct stat st;FILE *fp;char line[512];
 if(depth>4||++budget->files>8)return 0;
 fd=open(path,O_RDONLY|O_NOFOLLOW|O_NONBLOCK|O_CLOEXEC);if(fd<0)return 0;
 if(fstat(fd,&st)||!S_ISREG(st.st_mode)||st.st_size<0||st.st_size>262144){close(fd);return 0;}
 fp=fdopen(fd,"r");if(!fp){close(fd);return 0;}
 while(fgets(line,sizeof(line),fp)){
  char *key,*equal,*value,*end,*comment;size_t n=strlen(line);unsigned long parsed;
  budget->bytes+=n;if(budget->bytes>262144||(!strchr(line,'\n')&&!feof(fp))){ok=0;break;}
  comment=strchr(line,'#');if(comment)*comment=0;key=wr_iot_dns_trim(line);if(!*key)continue;
  equal=strchr(key,'=');if(!equal){if(!strcmp(key,"conf-dir")||!strcmp(key,"conf-file")||!strcmp(key,"port")){ok=0;break;}continue;}
  *equal=0;key=wr_iot_dns_trim(key);value=wr_iot_dns_trim(equal+1);
  if(!strcmp(key,"port")){
   if(!*value){ok=0;break;}
   for(end=value;*end;end++)if(!isdigit((unsigned char)*end)){ok=0;break;}
   if(!ok)break;
   parsed=strtoul(value,&end,10);if(*end||parsed>65535){ok=0;break;}*port=(unsigned int)parsed;
  }else if(!strcmp(key,"conf-file")){
   if(!*value)continue;
   if(strchr(value,',')||strchr(value,'"')||!wr_iot_dns_config_read(value,depth+1,budget,port)){ok=0;break;}
  }else if(!strcmp(key,"conf-dir")){ok=0;break;}
 }
 if(ferror(fp))ok=0;
 if(fclose(fp))ok=0;
 return ok;
}
static inline int wr_iot_dns_config_port(const char *path,unsigned int *out){
 struct wr_iot_dns_config_budget budget={0,0};unsigned int port=53;
 if(!path||!out||!wr_iot_dns_config_read(path,0,&budget,&port))return 0;
 *out=port;return 1;
}
#endif
