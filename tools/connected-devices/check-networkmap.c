#define _GNU_SOURCE
#include "networkmap.h"
#include <assert.h>
static struct wr_device_snapshot snapshot;
int main(void){FILE *fp=tmpfile();unsigned int i;assert(fp);
 assert(fputs("192.168.1.2,00:11:22:33:44:55,phone,1,1,0\n",fp)>=0);
 assert(fputs("192.168.1.3,02:11:22:33:44:55,name,with,commas,2,0,1\n",fp)>=0);
 assert(fputs("invalid,00:11:22:33:44:55,bad,1,0,0\n",fp)>=0);
 assert(fputs("192.168.1.4,invalid,bad,1,0,0\n",fp)>=0);
 rewind(fp);assert(wr_device_networkmap_read(fp,&snapshot));assert(snapshot.count==2&&snapshot.invalid==2&&!snapshot.truncated);
 assert(!strcmp(snapshot.records[1].name,"name,with,commas")&&snapshot.records[1].networkmap_stale==1);assert(!fclose(fp));
 fp=tmpfile();assert(fp);for(i=0;i<130;i++)assert(fputs("192.168.1.2,00:11:22:33:44:55,x,1,0,0\n",fp)>=0);rewind(fp);
 assert(wr_device_networkmap_read(fp,&snapshot)&&snapshot.count==128&&snapshot.truncated);assert(!fclose(fp));
 fp=tmpfile();assert(fp);for(i=0;i<800;i++)assert(fputc('x',fp)!=EOF);assert(fputc('\n',fp)!=EOF);
 assert(fputs("192.168.1.2,00:11:22:33:44:55,<img onerror=x>,1,0,0\n",fp)>=0);assert(fputs("partial",fp)>=0);rewind(fp);
 assert(wr_device_networkmap_read(fp,&snapshot)&&snapshot.count==1&&snapshot.invalid==2);assert(!strcmp(snapshot.records[0].name,"<img onerror=x>"));assert(!fclose(fp));
 puts("PASS bounded passive networkmap parser: six fields, comma names, invalid records, oversized lines, partial tail and disclosed truncation");return 0;
}
