/* Host simulation: never mounts or changes the real /tmp. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <sys/mount.h>
#include <sys/sysinfo.h>
#include <sys/vfs.h>
#include <sys/statvfs.h>
static int mock_statvfs(const char *path, struct statvfs *out)
{
 assert(strcmp(path, "/tmp") == 0);
 memset(out, 0, sizeof(*out));
 out->f_flag = ST_NOSUID;
 return 0;
}
static int scenario, reads, mounts;
static int mock_statfs(const char *path, struct statfs *out)
{
 assert(strcmp(path, "/tmp") == 0);
 reads++;
 if (scenario == 1 || (scenario == 4 && reads == 2)) return -1;
 memset(out, 0, sizeof(*out));
 out->f_type = scenario == 2 ? 0 : 0x01021994;
 out->f_bsize = 4096;
 out->f_blocks = (reads == 2 && scenario != 5 ? 50 : 24) * 256;
 out->f_bfree = out->f_blocks;
 return 0;
}
static int mock_sysinfo(struct sysinfo *out)
{
 memset(out, 0, sizeof(*out));
 out->mem_unit = 1;
 out->freeram = (scenario == 6 ? 16 : 80) * 1024UL * 1024UL;
 return 0;
}
static FILE *mock_fopen(const char *path, const char *mode)
{
 assert(strcmp(path, "/proc/meminfo") == 0);
 assert(strcmp(mode, "r") == 0);
 return NULL; /* Exercise conservative freeram fallback. */
}
static int mock_mount(const char *source, const char *path,
 const char *type, unsigned long flags, const void *data)
{
 mounts++;
 assert(source == NULL && strcmp(path, "/tmp") == 0);
 assert(strcmp(type, "tmpfs") == 0 && flags == (MS_REMOUNT | MS_NOSUID));
 assert(strcmp(data, "size=52428800") == 0);
 return scenario == 3 ? -1 : 0;
}
#define statfs(path, out) mock_statfs(path, out)
#define statvfs(path, out) mock_statvfs(path, out)
#define sysinfo(out) mock_sysinfo(out)
#define fopen(path, mode) mock_fopen(path, mode)
#define mount(source, path, type, flags, data) mock_mount(source, path, type, flags, data)
#include "tmp-upload-guard.h"
int main(void)
{
 unsigned long long limit;
 const int expected[] = {1, -1, -1, -3, -4, -4, -2};
 for (scenario = 0; scenario < 7; scenario++) {
  reads = mounts = 0; limit = 0;
  assert(wr_tmp_upload_increase(&limit) == expected[scenario]);
  assert(mounts == (scenario == 0 || scenario == 3 || scenario == 4 || scenario == 5));
  if (scenario == 0) assert(limit == 50);
  if (scenario >= 3) assert(limit == 24);
 }
 return 0;
}
