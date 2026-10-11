#ifndef WR_TMP_UPLOAD_GUARD_H
#define WR_TMP_UPLOAD_GUARD_H
#include <stdio.h>
#include <sys/mount.h>
#include <sys/sysinfo.h>
#include <sys/vfs.h>
#include <sys/statvfs.h>
#include "tmp-upload-policy.h"
/* Returns 1 on increased limit, 2 if already sufficient, negative on failure. */
static int wr_tmp_upload_increase(unsigned long long *limit_mib)
{
 struct statfs before, after;
 struct sysinfo memory;
 struct statvfs attributes;
 unsigned long mount_flags = MS_REMOUNT;
 unsigned long long available, used, current, desired, kib;
 int decision;
 FILE *stream;
 char line[256], options[64];
 if (!limit_mib || statfs("/tmp", &before) || before.f_type != 0x01021994 ||
     before.f_bsize <= 0 || before.f_bfree > before.f_blocks || sysinfo(&memory)) return -1;
 current = (unsigned long long)before.f_blocks * before.f_bsize;
 *limit_mib = current / WR_TMP_MIB;
 if (current >= 50 * WR_TMP_MIB) return 2;
 available = (unsigned long long)memory.freeram * (memory.mem_unit ? memory.mem_unit : 1);
 stream = fopen("/proc/meminfo", "r");
 if (stream) {
  while (fgets(line, sizeof(line), stream)) {
   if (sscanf(line, "MemAvailable: %llu kB", &kib) == 1) {
    available = kib * 1024ULL;
    break;
   }
  }
  fclose(stream);
 }
 used = (unsigned long long)(before.f_blocks - before.f_bfree) * before.f_bsize;
 decision = wr_tmp_upload_plan(current, used, available, &desired);
 if (decision != 1) return decision;
 if (statvfs("/tmp", &attributes) || (attributes.f_flag & ST_RDONLY)) return -1;
 if (attributes.f_flag & ST_NOSUID) mount_flags |= MS_NOSUID;
#ifdef ST_NODEV
 if (attributes.f_flag & ST_NODEV) mount_flags |= MS_NODEV;
#endif
#ifdef ST_NOEXEC
 if (attributes.f_flag & ST_NOEXEC) mount_flags |= MS_NOEXEC;
#endif
#ifdef ST_SYNCHRONOUS
 if (attributes.f_flag & ST_SYNCHRONOUS) mount_flags |= MS_SYNCHRONOUS;
#endif
#ifdef ST_NOATIME
 if (attributes.f_flag & ST_NOATIME) mount_flags |= MS_NOATIME;
#endif
#ifdef ST_NODIRATIME
 if (attributes.f_flag & ST_NODIRATIME) mount_flags |= MS_NODIRATIME;
#endif
#ifdef ST_RELATIME
 if (attributes.f_flag & ST_RELATIME) mount_flags |= MS_RELATIME;
#endif
 snprintf(options, sizeof(options), "size=%llu", desired);
 if (mount(NULL, "/tmp", "tmpfs", mount_flags, options)) return -3;
 if (statfs("/tmp", &after) || after.f_type != 0x01021994 || after.f_bsize <= 0) return -4;
 *limit_mib = ((unsigned long long)after.f_blocks * after.f_bsize) / WR_TMP_MIB;
 if (*limit_mib * WR_TMP_MIB < desired) return -4;
 return 1;
}
#endif
