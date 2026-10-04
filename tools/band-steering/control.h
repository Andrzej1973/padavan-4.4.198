#ifndef WR_BAND_CONTROL_H
#define WR_BAND_CONTROL_H
#include "session.h"
#include <sys/types.h>
/* The caller holds the daemon owner lock for the endpoint lifetime. */
struct wr_band_control { int fd; char path[108]; dev_t device; ino_t inode; };
int wr_band_control_open(struct wr_band_control *, const char *path);
void wr_band_control_close(struct wr_band_control *);
/* One nonblocking datagram. Invalid/untrusted requests have no state effect.
 * STOP acknowledgement means requested, never proof of driver OFF. */
int wr_band_control_receive(struct wr_band_control *, enum wr_band_phase, int *stop_requested);
const char *wr_band_control_status(enum wr_band_phase);
#endif

