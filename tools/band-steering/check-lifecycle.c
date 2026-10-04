#include "lifecycle.h"
#include <assert.h>
#include <stdio.h>
struct fixture { int calls[12], count, fail, off_calls, cleanup_fail; };
static int step(struct fixture *f, int id) { f->calls[f->count++] = id; return f->fail == id ? -1 : 0; }
static int validate(void *p) { return step(p, 1); }
static int off(void *p) { struct fixture *f=p; ++f->off_calls; return step(f, 2) || (f->off_calls>1 && f->cleanup_fail); }
static int profiles(void *p, int enabled) { assert(enabled==0 || enabled==1); return step(p, 3); }
static int radios(void *p) { return step(p, 4); }
static int start(void *p) { return step(p, 5); }
int main(void) {
    struct wr_band_lifecycle_ops ops={validate,off,profiles,radios,start};
    struct wr_band_apply_result r; struct fixture f={0}; int failure;
    assert(!wr_band_lifecycle_apply(&ops,&f,1,&r) && r.state==WR_APPLY_RUNNING && !r.off_confirmed);
    for (failure=1;failure<=5;++failure) {
        f=(struct fixture){0}; f.fail=failure;
        assert(wr_band_lifecycle_apply(&ops,&f,1,&r)==-1);
        if (failure==1) assert(f.count==1);
        if (failure==2) assert(f.count==2 && !r.off_confirmed);
        if (failure==3) assert(f.count==3 && r.off_confirmed);
        if (failure>=4) assert(f.calls[f.count-1]==2 && r.off_confirmed);
    }
    f=(struct fixture){0}; f.fail=5; f.cleanup_fail=1;
    assert(wr_band_lifecycle_apply(&ops,&f,1,&r)==-1 && !r.off_confirmed);
    f=(struct fixture){0};
    assert(!wr_band_lifecycle_apply(&ops,&f,0,&r) && r.off_confirmed && f.count==3);
    assert(f.calls[0]==2 && f.calls[1]==3 && f.calls[2]==4);
    puts("PASS lifecycle ordering and failure cleanup with mocked operations; rc/device integration pending");
    return 0;
}
