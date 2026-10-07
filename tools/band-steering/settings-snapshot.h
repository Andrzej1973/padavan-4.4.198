#ifndef WR_BAND_SETTINGS_SNAPSHOT_H
#define WR_BAND_SETTINGS_SNAPSHOT_H
#include <stddef.h>
struct wr_band_settings_snapshot { char *data; size_t capacity; };
typedef int (*wr_band_snapshot_reader)(char *, int, int);
/* Initialize to {0}. Reader must report overflow, not silently truncate.
 * The patched NVRAM getall implementation supplies that contract. */
int wr_band_snapshot_capture(struct wr_band_settings_snapshot *, size_t, wr_band_snapshot_reader);
const char *wr_band_snapshot_get(const struct wr_band_settings_snapshot *, const char *);
void wr_band_snapshot_release(struct wr_band_settings_snapshot *);
#endif
