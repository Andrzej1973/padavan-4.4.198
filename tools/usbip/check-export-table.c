#include <assert.h>
#include <limits.h>
static char target_dir[PATH_MAX];
#define WR_USBIP_EXPORT_DIRECTORY target_dir
#define main wr_usbip_test_reader_main
#include "export-table.c"
#undef main
static int capture(char out[1024])
{
 char *args[]={"export-table","--list",NULL};int saved=dup(1),result;size_t n;FILE *fp=tmpfile();
 assert(saved>=0&&fp);assert(dup2(fileno(fp),1)==1);
 result=wr_usbip_test_reader_main(2,args);assert(fflush(stdout)==0);
 assert(dup2(saved,1)==1&&close(saved)==0);rewind(fp);
 n=fread(out,1,1023,fp);out[n]=0;assert(fclose(fp)==0);return result;
}
int main(void)
{
 char root[]="/tmp/wr-usbip-table-XXXXXX",out[1024],path[PATH_MAX];
 struct wr_usbip_export_rule rules[16]={0};FILE *fp;
 assert(mkdtemp(root));snprintf(target_dir,sizeof(target_dir),"%s/storage",root);
 assert(capture(out)==0&&!out[0]);assert(access(target_dir,F_OK)!=0);
 assert(mkdir(target_dir,0700)==0);rules[0].enabled=1;strcpy(rules[0].bus,"1-1");
 strcpy(rules[0].vendor,"1234");strcpy(rules[0].product,"abcd");strcpy(rules[0].serial_hex,"756e6974");
 assert(wr_usbip_export_save_locked(target_dir,rules)==WR_USBIP_STORE_SAVED);
 assert(capture(out)==0&&!strcmp(out,"1-1\t1234\tabcd\t756e6974\n"));
 assert(snprintf(path,sizeof(path),"%s/exports.v1",target_dir)<(int)sizeof(path));
 fp=fopen(path,"w");assert(fp);assert(fputs("invalid\n",fp)>=0&&fclose(fp)==0);
 assert(capture(out)==2&&!out[0]);assert(unlink(path)==0);
 assert(symlink("missing",path)==0);assert(capture(out)==2&&!out[0]);assert(unlink(path)==0);
 assert(rmdir(target_dir)==0&&rmdir(root)==0);
 puts("PASS USBIP table reader: private validated output, missing default, corrupt and symlink refusal");return 0;
}
