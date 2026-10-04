#include "control-client.h"
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
int main(int argc, char **argv)
{
    pid_t expected_pid = 0;
    char reply[64];
    if (argc == 2 && !strcmp(argv[1], "--help")) {
        puts("Usage: wr-band-steering-ctl status|stop|status-pid PID\n"
             "STOP acknowledges a request, not proof that radios stopped steering.");
        return 0;
    }
    if (argc == 3 && !strcmp(argv[1], "status-pid")) {
        char *end;
        long parsed;
        const char *digit;
        if (!argv[2][0]) return 2;
        for (digit = argv[2]; *digit; ++digit)
            if (*digit < '0' || *digit > '9') return 2;
        errno = 0;
        parsed = strtol(argv[2], &end, 10);
        expected_pid = (pid_t)parsed;
        if (errno || *end || parsed <= 1 || (long)expected_pid != parsed) return 2;
    } else if (argc != 2 || (strcmp(argv[1], "status") && strcmp(argv[1], "stop"))) {
        fprintf(stderr, "Use --help for usage.\n"); return 2;
    }
    if (geteuid() != 0) { fprintf(stderr, "Root is required.\n"); return 2; }
    if (wr_band_control_request(expected_pid, !strcmp(argv[1], "stop"), reply)) return 1;
    return fputs(reply, stdout) == EOF ? 1 : 0;
}
