/* Read-only validated table reader for a lifecycle-lock owner.
 * stdout contains private serial identifiers; never copy into public logs.
 * This program performs no bind/unbind, module load or flash write. */
#include "export-store.h"
#ifndef WR_USBIP_EXPORT_DIRECTORY
#define WR_USBIP_EXPORT_DIRECTORY "/etc/storage/usbip"
#endif
int main(int argc,char **argv)
{
 struct wr_usbip_export_rule *rules;struct stat s;int dir;size_t i;
 if(argc!=2||strcmp(argv[1],"--list"))return 2;
 dir=wr_usbip_store_directory(WR_USBIP_EXPORT_DIRECTORY);
 if(dir<0)return errno==ENOENT?0:2;
 if(fstatat(dir,"exports.v1",&s,AT_SYMLINK_NOFOLLOW)){
  int absent=errno==ENOENT;close(dir);return absent?0:2;
 }
 close(dir);rules=calloc(16,sizeof(*rules));if(!rules)return 2;
 if(!wr_usbip_export_load_locked(WR_USBIP_EXPORT_DIRECTORY,rules)){free(rules);return 2;}
 /* No output until the complete file and all identities have been validated. */
 for(i=0;i<16;i++)if(rules[i].enabled)
  if(printf("%s\t%s\t%s\t%s\n",rules[i].bus,rules[i].vendor,rules[i].product,rules[i].serial_hex)<0){free(rules);return 2;}
 free(rules);return fflush(stdout)==0?0:2;
}
