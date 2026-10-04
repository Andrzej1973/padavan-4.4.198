#include "control.h"
#include <poll.h>
#include <stdio.h>
/* Host fixture only: exercises real local IPC, never accesses drivers. */
int main(int argc, char **argv)
{
    struct wr_band_control c;
    struct pollfd ready;
    int stop = 0, result = 1;
    if (argc != 2 || wr_band_control_open(&c, argv[1])) return 1;
    puts("READY"); fflush(stdout);
    ready.fd = c.fd; ready.events = POLLIN;
    while (!stop) {
        ready.revents = 0;
        if (poll(&ready, 1, 5000) != 1 || !(ready.revents & POLLIN)) goto done;
        if (wr_band_control_receive(&c, WR_ACTIVE, &stop) < 0) goto done;
    }
    result = 0;
done:
    wr_band_control_close(&c); return result;
}
