#include <assert.h>
#include "export-store.h"
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
 rules[0].serial_hex[0]=0;assert(wr_usbip_export_save_locked(directory,rules)==WR_USBIP_STORE_REFUSED);
 assert(wr_usbip_export_load_locked(directory,loaded));assert(!memcmp(before,loaded,sizeof(before)));
 snprintf(path,sizeof(path),"%s/exports.v1",directory);assert(unlink(path)==0);
 assert(symlink("missing",path)==0);assert(!wr_usbip_export_load_locked(directory,loaded));
 rules[0].enabled=0;assert(wr_usbip_export_save_locked(directory,rules)==WR_USBIP_STORE_REFUSED);
 assert(!memcmp(before,loaded,sizeof(before)));assert(unlink(path)==0);
 assert(chmod(directory,0777)==0);assert(wr_usbip_export_save_locked(directory,rules)==WR_USBIP_STORE_REFUSED);
 assert(chmod(directory,0700)==0);assert(rmdir(directory)==0);
 puts("PASS USBIP export store: roundtrip, invalid table preservation, symlink and directory refusal");return 0;
}
