/* Read the effective DNS port from bounded regular config files.
 * Directory ordering and suffix filters follow the pinned dnsmasq 2.93 implementation. */
#ifndef WR_IOT_DNS_CONFIG_H
#define WR_IOT_DNS_CONFIG_H
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>
#include <dirent.h>
#include <errno.h>
struct wr_iot_dns_config_budget {unsigned int files;size_t bytes;};
static inline char *wr_iot_dns_trim(char *value){
 char *end;while(isspace((unsigned char)*value))value++;
 end=value+strlen(value);while(end>value&&isspace((unsigned char)end[-1]))*--end=0;
 return value;
}
/* dnsmasq comments start at a whitespace boundary outside double quotes.
 * Preserve quote syntax for the option-specific parser rather than truncating paths. */
static inline int wr_iot_dns_config_comments(char *line){
 char *p;int quoted=0,white=1;
 for(p=line;*p;p++){
  if(quoted){
   if(*p=='\\'&&p[1]&&strchr("\"tnebr\\",p[1])){p++;continue;}
   if(*p=='"')quoted=0;
   continue;
  }
  if(*p=='"'){quoted=1;white=0;continue;}
  if(white&&*p=='#'){*p=0;break;}
  white=isspace((unsigned char)*p)!=0;
 }
 return !quoted;
}
static inline int wr_iot_dns_config_read(const char *,unsigned int,struct wr_iot_dns_config_budget *,unsigned int *);
static inline int wr_iot_dns_config_dir(char *spec,unsigned int depth,struct wr_iot_dns_config_budget *budget,unsigned int *port){
 char *filters[8],*save=NULL,*directory,*token;char paths[8][512],temp[512];
 unsigned int nf=0,count=0,entries=0,i,j;int fd,ok=1;DIR *dir;struct dirent *entry;
 directory=strtok_r(spec,",",&save);if(!directory||!*directory)return 0;
 while((token=strtok_r(NULL,",",&save))){if(nf==8)return 0;filters[nf++]=token;}
 fd=open(directory,O_RDONLY|O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC);if(fd<0)return 0;
 dir=fdopendir(fd);if(!dir){close(fd);return 0;}
 errno=0;
 while((entry=readdir(dir))){
  size_t n=strlen(entry->d_name);int matched=0,required=0,ignored=0,written;struct stat st;
  if(++entries>256){ok=0;break;}
  if(!n||entry->d_name[0]=='.'||entry->d_name[n-1]=='~'||(entry->d_name[0]=='#'&&entry->d_name[n-1]=='#'))continue;
  for(i=0;i<nf;i++){
   const char *suffix=filters[i];size_t length;
   if(*suffix=='*'){if(!suffix[1])continue;required=1;suffix++;length=strlen(suffix);if(n>length&&!strcmp(entry->d_name+n-length,suffix))matched=1;}
   else {length=strlen(suffix);if(n>length&&!strcmp(entry->d_name+n-length,suffix))ignored=1;}
  }
  if(ignored||(required&&!matched))continue;
  if(fstatat(dirfd(dir),entry->d_name,&st,AT_SYMLINK_NOFOLLOW)){ok=0;break;}
  if(S_ISLNK(st.st_mode)){ok=0;break;}
  if(!S_ISREG(st.st_mode))continue;
  if(count==8){ok=0;break;}
  written=snprintf(paths[count],sizeof(paths[count]),"%s/%s",directory,entry->d_name);
  if(written<0||(size_t)written>=sizeof(paths[count])){ok=0;break;}
  count++;errno=0;
 }
 if(errno)ok=0;
 if(closedir(dir))ok=0;
 if(!ok)return 0;
 for(i=0;i<count;i++)for(j=i+1;j<count;j++)if(strcmp(paths[i],paths[j])>0){strcpy(temp,paths[i]);strcpy(paths[i],paths[j]);strcpy(paths[j],temp);}
 for(i=0;i<count;i++)if(!wr_iot_dns_config_read(paths[i],depth+1,budget,port))return 0;
 return 1;
}
static inline int wr_iot_dns_config_read(const char *path,unsigned int depth,struct wr_iot_dns_config_budget *budget,unsigned int *port){
 int fd,ok=1;struct stat st;FILE *fp;char line[512];
 if(depth>4||++budget->files>8)return 0;
 fd=open(path,O_RDONLY|O_NOFOLLOW|O_NONBLOCK|O_CLOEXEC);if(fd<0)return 0;
 if(fstat(fd,&st)||!S_ISREG(st.st_mode)||st.st_size<0||st.st_size>262144){close(fd);return 0;}
 fp=fdopen(fd,"r");if(!fp){close(fd);return 0;}
 while(fgets(line,sizeof(line),fp)){
  char *key,*equal,*value,*end;size_t n=strlen(line);unsigned long parsed;
  budget->bytes+=n;if(budget->bytes>262144||(!strchr(line,'\n')&&!feof(fp))){ok=0;break;}
  if(!wr_iot_dns_config_comments(line)){ok=0;break;}key=wr_iot_dns_trim(line);if(!*key)continue;
  equal=strchr(key,'=');if(!equal){if(!strcmp(key,"conf-dir")||!strcmp(key,"conf-script")||!strcmp(key,"conf-file")||!strcmp(key,"port")){ok=0;break;}continue;}
  *equal=0;key=wr_iot_dns_trim(key);value=wr_iot_dns_trim(equal+1);
  if(!strcmp(key,"port")){
   if(!*value){ok=0;break;}
   for(end=value;*end;end++)if(!isdigit((unsigned char)*end)){ok=0;break;}
   if(!ok)break;
   parsed=strtoul(value,&end,10);if(*end||parsed>65535){ok=0;break;}*port=(unsigned int)parsed;
  }else if(!strcmp(key,"conf-file")){
   if(!*value)continue;
   if(strchr(value,',')||strchr(value,'"')||!wr_iot_dns_config_read(value,depth+1,budget,port)){ok=0;break;}
  }else if(!strcmp(key,"conf-dir")){if(!wr_iot_dns_config_dir(value,depth,budget,port)){ok=0;break;}}
  else if(!strcmp(key,"conf-script")){ok=0;break;}
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
