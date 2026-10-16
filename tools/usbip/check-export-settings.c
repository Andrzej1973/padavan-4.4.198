#include <assert.h>
#include <limits.h>
static char settings_dir[PATH_MAX],settings_lock[PATH_MAX];
#define WR_USBIP_EXPORT_DIRECTORY settings_dir
#define WR_USBIP_LIFECYCLE_LOCK settings_lock
#include "export-settings.h"
int main(void)
{
 char root[]="/tmp/wr-usbip-settings-XXXXXX",file[PATH_MAX];int held;
 struct wr_usbip_export_rule rules[16]={0},out[16],before[16];
 assert(mkdtemp(root));snprintf(settings_dir,sizeof(settings_dir),"%s/storage",root);
 snprintf(settings_lock,sizeof(settings_lock),"%s/lock",root);
 memset(out,0x5a,sizeof(out));memcpy(before,out,sizeof(out));
 held=wr_usbip_settings_lock();assert(held>=0);
 assert(wr_usbip_settings_read(out)==WR_USBIP_SETTINGS_BUSY);assert(!memcmp(before,out,sizeof(out)));
 assert(wr_usbip_settings_save(rules)==WR_USBIP_STORE_REFUSED);close(held);
 assert(access(settings_dir,F_OK)!=0);
 assert(wr_usbip_settings_read(out)==WR_USBIP_SETTINGS_EMPTY);assert(!memcmp(out,rules,sizeof(out)));
 assert(wr_usbip_settings_save(rules)==WR_USBIP_STORE_SAVED);
 assert(wr_usbip_settings_read(out)==WR_USBIP_SETTINGS_READY);
 assert(!memcmp(out,rules,sizeof(out)));
 assert(unlink(settings_lock)==0);assert(symlink("missing",settings_lock)==0);
 assert(wr_usbip_settings_save(rules)==WR_USBIP_STORE_REFUSED);
 assert(unlink(settings_lock)==0);
 assert(snprintf(file,sizeof(file),"%s/exports.v1",settings_dir)<(int)sizeof(file));
 assert(unlink(file)==0&&rmdir(settings_dir)==0&&rmdir(root)==0);
 puts("PASS USBIP settings: shared lock contention, default-empty state and private persistence");return 0;
}
