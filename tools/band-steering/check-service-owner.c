#include "service-owner.h"
#include "child-owner.h"
#include <assert.h>
#include <stdio.h>
static int stop_result, retain_pid, quiesce_result, start_result;
static int stops, quiesces, starts;
static int writes, initialized, validations;
static int validate(void *p) { assert(p == &writes); ++validations; return 0; }
static int profiles(void *p, int enabled)
{ assert(p == &writes && (enabled == 0 || enabled == 1)); assert(!writes && !initialized); ++writes; return 0; }
static int radios(void *p)
{ assert(p == &writes && writes == 1); ++initialized; return 0; }
int wr_band_child_stop(pid_t *pid, unsigned timeout)
{
    assert(*pid == 42 && timeout == 5000); ++stops;
    if (!retain_pid) *pid = 0;
    return stop_result;
}
int wr_band_child_quiesce(pid_t *pid, const char *a, const char *b)
{
    assert(!*pid && a && b); ++quiesces;
    if (quiesce_result) *pid = 43;
    return quiesce_result;
}
int wr_band_child_start_verified(pid_t *pid, const char *a, const char *b, unsigned timeout)
{
    assert(!*pid && a && b && timeout == 5000); ++starts;
    *pid = 42; return start_result;
}
int main(void)
{
    struct wr_band_service_owner owner = {0};
    assert(!wr_band_service_quiesce(&owner,"ra0","rai0") && quiesces == 1);
    assert(!wr_band_service_start(&owner,"ra0","rai0") && owner.pid == 42);
    assert(wr_band_service_start(&owner,"ra0","rai0") == -1 && starts == 1);
    retain_pid = 1; stop_result = -1;
    assert(wr_band_service_quiesce(&owner,"ra0","rai0") == -1);
    assert(owner.pid == 42 && quiesces == 1);
    retain_pid = 0;
    assert(!wr_band_service_quiesce(&owner,"ra0","rai0"));
    assert(!owner.pid && quiesces == 2);
    owner.pid = 42; stop_result = 0;
    assert(!wr_band_service_quiesce(&owner,"ra0","rai0") && quiesces == 2);
    quiesce_result = -1;
    assert(wr_band_service_quiesce(&owner,"ra0","rai0") == -1 && owner.pid == 43);
    assert(wr_band_service_start(&owner,"ra0","rai0") == -1 && starts == 1);
    owner.pid = 0; start_result = -1;
    assert(wr_band_service_start(&owner,"ra0","rai0") == -1 && owner.pid == 42);
    assert(stops == 3);
    assert(wr_band_service_quiesce(0,"ra0","rai0") == -1);
    assert(wr_band_service_start(0,"ra0","rai0") == -1);
    {
        struct wr_band_lifecycle_ops ops = {validate, 0, profiles, radios, 0};
        struct wr_band_apply_result result;
        owner.pid = 0; quiesce_result = 0; start_result = 0;
        assert(!wr_band_service_apply(&owner,"ra0","rai0",&ops,&writes,1,&result));
        assert(result.state == WR_APPLY_RUNNING && !result.off_confirmed);
        assert(owner.pid == 42 && validations == 1 && writes == 1 && initialized == 1);
        writes = initialized = 0;
        assert(!wr_band_service_apply(&owner,"ra0","rai0",&ops,&writes,0,&result));
        assert(result.state == WR_APPLY_OFF_CONFIRMED && result.off_confirmed && !owner.pid);
        assert(validations == 1 && writes == 1 && initialized == 1);
        assert(wr_band_service_apply(&owner,"ra0","rai0",0,&writes,0,&result) == -1);
        assert(result.state == WR_APPLY_REJECTED && !result.off_confirmed);
    }
    puts("PASS service ownership ordering/PID retention with mocked child operations; device behavior unverified");
    return 0;
}
