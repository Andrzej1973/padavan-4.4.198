#include <assert.h>
#include <errno.h>
#include <sys/stat.h>
#include <unistd.h>
static int fail_directory_fsync;
static int wr_usbip_test_fsync(int fd);
#define WR_USBIP_FSYNC(fd) wr_usbip_test_fsync(fd)
#include "export-store.h"
#undef WR_USBIP_FSYNC

static int wr_usbip_test_fsync(int fd)
{
 struct stat s;
 if(fail_directory_fsync&&fstat(fd,&s)==0&&S_ISDIR(s.st_mode)){errno=EIO;return -1;}
 return fsync(fd);
}

int main(void)
{
 char directory[]="/tmp/wr-usbip-exports-XXXXXX",path[512];
 struct wr_usbip_export_rule rules[16]={0},loaded[16],before[16];
 assert(mkdtemp(directory));
 assert(wr_usbip_export_save_locked(directory,rules)==WR_USBIP_STORE_SAVED);
 assert(wr_usbip_export_load_locked(directory,loaded));assert(!memcmp(rules,loaded,sizeof(rules)));
 rules[0].enabled=1;strcpy(rules[0].bus,"1-1");strcpy(rules[0].vendor,"1234");
 strcpy(rules[0].product,"abcd");strcpy(rules[0].serial_hex,"756e6974");
 assert(wr_usbip_export_save_locked(directory,rules)==WR_USBIP_STORE_SAVED);
 assert(wr_usbip_export_load_locked(directory,loaded));memcpy(before,loaded,sizeof(before));
 strcpy(rules[0].product,"beef");fail_directory_fsync=1;
 assert(wr_usbip_export_save_locked(directory,rules)==WR_USBIP_STORE_UNCONFIRMED);
 fail_directory_fsync=0;assert(wr_usbip_export_load_locked(directory,loaded));
 assert(!strcmp(loaded[0].product,"beef"));
 memcpy(before,loaded,sizeof(before));
 rules[0].serial_hex[0]=0;assert(wr_usbip_export_save_locked(directory,rules)==WR_USBIP_STORE_REFUSED);
 assert(wr_usbip_export_load_locked(directory,loaded));assert(!memcmp(before,loaded,sizeof(before)));
 snprintf(path,sizeof(path),"%s/exports.v1",directory);assert(unlink(path)==0);
 assert(symlink("missing",path)==0);assert(!wr_usbip_export_load_locked(directory,loaded));
 rules[0].enabled=0;assert(wr_usbip_export_save_locked(directory,rules)==WR_USBIP_STORE_REFUSED);
 assert(!memcmp(before,loaded,sizeof(before)));assert(unlink(path)==0);
 assert(chmod(directory,0777)==0);assert(wr_usbip_export_save_locked(directory,rules)==WR_USBIP_STORE_REFUSED);
 assert(chmod(directory,0700)==0);assert(rmdir(directory)==0);
 puts("PASS USBIP export store: roundtrip, directory-fsync uncertainty, invalid table preservation, symlink and directory refusal");return 0;
}
