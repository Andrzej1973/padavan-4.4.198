#!/usr/bin/env python3
"""Extract actual bridge read helpers; fake I/O is not sysfs/kernel evidence."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('source',type=Path)
p.add_argument('output',type=Path)
a=p.parse_args()
source=a.source.read_text(encoding='utf-8')
functions=[]
for name in ('owned','empty_bridge','sole_bss_member','ipv6_disabled'):
    anchor='static int '+name+'(void) {'
    if source.count(anchor)!=1:
        raise SystemExit('Bridge reader missing or duplicated: '+name)
    start=source.index(anchor)
    functions.append(source[start:source.index('\n}',start)+2])
a.output.write_text(r'''#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#define IOT_OWNER "wr1200js-iot-v1"
#define IOT_BSS "ra2"
typedef struct {int unused;} DIR;
struct dirent {char d_name[32];};
struct stat {int st_mode;};
#define S_ISDIR(mode) ((mode)==1)
#define F_OK 0
static int file_close_error,read_error,trailing,directory_error,directory_close_error;
static int directory_missing,member_kind,read_index,access_error,opens,closed;
static const char *file_text=IOT_OWNER "\n";
static struct dirent member;
static DIR directory;
static int fixture_stat(const char *path,struct stat *s){assert(path);s->st_mode=1;return 0;}
static FILE *fixture_fopen(const char *path,const char *mode){assert(path&&mode);opens++;return (FILE *)&directory;}
static char *fixture_fgets(char *out,int size,FILE *f){
 assert(f&&size>0);if(!file_text)return NULL;
 snprintf(out,(size_t)size,"%s",file_text);return out;
}
static int fixture_ferror(FILE *f){assert(f);return read_error;}
static int fixture_fgetc(FILE *f){assert(f);return trailing?'x':EOF;}
static int fixture_fclose(FILE *f){assert(f);closed++;return file_close_error;}
static DIR *opendir(const char *path){assert(path);read_index=0;return directory_missing?NULL:&directory;}
static struct dirent *readdir(DIR *d){
 assert(d==&directory);
 if(read_index++==0&&member_kind){strcpy(member.d_name,member_kind==1?"ra2":"foreign");return &member;}
 if(directory_error)errno=EIO;
 return NULL;
}
static int closedir(DIR *d){assert(d==&directory);return directory_close_error;}
static int access(const char *path,int mode){assert(path&&mode==F_OK);if(access_error){errno=access_error;return -1;}return 0;}
#define stat(path,out) fixture_stat(path,out)
#define fopen fixture_fopen
#define fgets fixture_fgets
#define ferror fixture_ferror
#define fgetc fixture_fgetc
#define fclose fixture_fclose
'''+ '\n'.join(functions)+r'''
int main(void){
 assert(owned());file_close_error=1;assert(!owned());file_close_error=0;
 read_error=1;assert(!owned());read_error=0;trailing=1;assert(!owned());trailing=0;
 file_text="wr1200js-iot-v1-extra\n";assert(!owned());file_text=NULL;assert(!owned());
 assert(opens==closed);
 assert(empty_bridge());directory_error=1;assert(!empty_bridge());directory_error=0;
 directory_close_error=1;assert(!empty_bridge());directory_close_error=0;
 member_kind=1;assert(!empty_bridge()&&sole_bss_member());
 directory_error=1;assert(!sole_bss_member());directory_error=0;
 directory_close_error=1;assert(!sole_bss_member());directory_close_error=0;
 member_kind=2;assert(!sole_bss_member());directory_missing=1;
 assert(!empty_bridge()&&!sole_bss_member());directory_missing=0;
 file_text="1\n";assert(ipv6_disabled());file_text="0\n";assert(!ipv6_disabled());
 file_text="1 extra\n";assert(!ipv6_disabled());file_text="1\n";
 read_error=1;assert(!ipv6_disabled());read_error=0;
 trailing=1;assert(!ipv6_disabled());trailing=0;
 file_close_error=1;assert(!ipv6_disabled());file_close_error=0;
 access_error=ENOENT;assert(ipv6_disabled());access_error=EACCES;assert(!ipv6_disabled());
 puts("PASS actual bridge read helpers: alias completeness, directory read/close failures, sole membership and exact IPv6 gate; I/O injected");
 return 0;
}
''',encoding='utf-8')
print('Prepared actual bridge reader fixture with injected I/O')
