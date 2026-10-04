#define _POSIX_C_SOURCE 200809L
#include "child-owner.h"
#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <unistd.h>
int main(void)
{
    pid_t pid = 0;
    assert(geteuid() == 0);
    assert(!wr_band_child_start_verified(&pid, "ra0", "rai0", 3000) && pid > 1);
    assert(!wr_band_child_stop(&pid, 1000) && !pid);
    assert(wr_band_child_start_verified(&pid, "ra1", "rai0", 200) == -1);
    assert(errno == ETIMEDOUT && pid > 1);
    assert(!wr_band_child_stop(&pid, 1000) && !pid);
    assert(wr_band_child_start_verified(&pid, "ra2", "rai0", 3000) == -1);
    assert(errno == ECHILD && pid > 1);
    assert(wr_band_child_stop(&pid, 1000) == -1 && errno == EIO && !pid);
    assert(!wr_band_child_quiesce(&pid, "ra0", "rai0") && !pid);
    assert(wr_band_child_quiesce(&pid, "ra1", "rai0") == -1 && errno == EIO && !pid);
    puts("PASS actual foreground spawn, authenticated ACTIVE wait, timeout retains ownership and failed child cleanup; no driver access");
    return 0;
}
