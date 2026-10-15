/* Target adapter; only libshared NVRAM reads, no setters or flash commit. */
#define WR_EOIP_WORKER_NO_MAIN
#include "worker.c"
#include "stored.h"
#include "nvram_linux.h"
#include <signal.h>
#include <sys/wait.h>
static const char *wr_eoip_nvram_read(void *context, const char *key)
{ (void)context; return nvram_get(key); }
static int wr_eoip_target_query(void *context, const char *name, const char *owner,
                                struct wr_eoip_observation *out)
{ (void)context; return wr_eoip_query_link(name, owner, out); }
static int wr_eoip_load_module(void *context)
{
    pid_t child, waited;
    unsigned attempt;
    int status;
    (void)context;
    signal(SIGCHLD, SIG_DFL);
    child = fork();
    if (child < 0) return 0;
    if (!child) {
        execl("/sbin/modprobe", "modprobe", "eoip", (char *)NULL);
        _exit(127);
    }
    for (attempt = 0; attempt < 1000; attempt++) {
        waited = waitpid(child, &status, WNOHANG);
        if (waited == child) return WIFEXITED(status) && !WEXITSTATUS(status);
        if (waited < 0 && errno != EINTR) return 0;
        usleep(10000);
    }
    kill(child, SIGKILL);
    for (attempt = 0; attempt < 10; attempt++) {
        waited = waitpid(child, &status, WNOHANG);
        if (waited == child || (waited < 0 && errno == ECHILD)) break;
        usleep(10000);
    }
    /* This short-lived command now exits; init inherits a child not reapable
     * after cancellation. Never synchronously wait on a stuck module load. */
    return 0;
}
int main(int argc, char **argv)
{
    struct wr_eoip_transport transport = {NULL, wr_eoip_socket_talk, wr_eoip_target_query};
    struct wr_eoip_worker worker = {&transport, WR_EOIP_WORKER_DIRECTORY};
    char message[WR_EOIP_WORKER_MESSAGE] = "";
    int result;
    if (argc == 2 && (!strcmp(argv[1], "boot-stored") || !strcmp(argv[1], "apply-stored")))
        result = wr_eoip_stored_dispatch(&worker, argv[1], wr_eoip_nvram_read, NULL,
            wr_eoip_load_module, message, sizeof(message));
    else result = wr_eoip_worker_dispatch(&worker, argc, argv, message, sizeof(message));
    fprintf(result ? stderr : stdout, "%s\n", message);
    return result;
}
