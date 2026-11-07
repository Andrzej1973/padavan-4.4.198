# Owned APCLI/Monitor family close76 — isolated candidate host verification

prepare-aux-family-close-owner.py pins five candidate75 files, adds per-slot
family-close state to the adapter and initializes it with registry slots.
Both real ndo_stop wrappers now delegate to one shared owned-close fragment
with their respective family ioctl callbacks. It reserves exact auxiliary
ownership before family mutation; no family ioctl runs under the spinlock.
The state stores device/generation/serial/epoch/open token. Failure retains
CLOSING and module ownership; repeated ndo_stop does not replay family ioctl.
Family success, DOWN result and final reference consumption are distinct.
The helper deliberately refuses the last reference: physical-close recovery
is not implemented by this non-last binding.

The family model was strengthened to reject stale epoch/open-token identity.
The shared actual DOWN fragment now compares ticket epoch under the same lock
before changing virtual count. An early check in the owned helper cannot
replace that atomic downstream revalidation. HNAT/other unlocked effects may
occur before a reset is noticed; those effects require retained reconciliation,
not rollback or automatic replay.

Test candidate: .iot-local-check/aux-owned76b-20261030.
prepare-aux-family-owned-check.py composes the actual two wrappers, owned
fragment and actual DOWN body with mocked driver/kernel operations. Strict
GCC C11/O2/Wall/Wextra/Werror base/HNAT variants passed last-reference refusal,
family failure, repeated entry refusal, unmutated DOWN failure retention,
success/final module consumption, reset during family ioctl and (HNAT variant)
reset between family confirmation and DOWN. The latter leaves count unchanged.
Standalone stronger family-stage identity model also passed.

Earlier seam builds exposed quoted-include selection of old tool headers;
the corrected fixture includes candidate close-claim before the family model.
A subsequent compile identified a missing NDIS_STATUS_FAILURE test constant;
the fixture was corrected without weakening warnings. Those failed drafts
remain local. Their exec sessions are terminal; no live tests remain.

Limits: actual kernel locks/RTNL, HNAT, module refs, ioctls and allocation are
mocked. Adapter layout/initialization and native/OS_ABL target ABI are not
compiled. Added state size is not measured for target. Real APCLI/Monitor OPEN
registry acquisition must also be bound/verified; seeded OWNED host records
are not proof that live OPEN reaches this state. No deferred recovery worker,
last-close implementation, callback retirement or final PCI release acceptance.
Candidate76 is isolated, not added to the main chain (which currently ends75).
Old legacy endpoint fixtures need adaptation to the new wrappers before broad
composition replay. Last full host replay74 passed76 variants; last fresh
whole source chain70. No production install, firmware build, router mutation,
CI dispatch, commit or push in this step.
