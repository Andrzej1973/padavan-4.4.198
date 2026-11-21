# Optional1387: RC map option attached to the wrong make target

Run44318237538, requested5fa12e65722cc7d35c7a4fca8c9f41747ce471df,
failed in Compile isolated merged IoT MT7603 candidate. Monitor1352/run44321453814
identified that step and the actionable error. Original job134850084380 confirms:

```text
ValueError: Missing/linked selector evidence: rc-link-map.txt
```

The monitor also included nonfatal compiler-source messages and cache counters,
but preserved the actual cause. No monitor parser change was needed; unrelated
local Nim monitor edits remain untouched.

The real native RC Makefile has `EXEC = rc`, but its recipe is:

```make
all: $(OBJS) Makefile
	$(CC) -o $(EXEC) $(OBJS) $(LDFLAGS)
	$(STRIP) $(EXEC)
```

The5fa script appended a target-specific `rc: override LDFLAGS += ...`.
Its outer build invokes `make ... all`, which directly links the binary;
there is no dependency on a `rc` recipe. The option was absent from the actual
link command. RC/HTTP linking completed before the evidence verifier refused
the missing map. The earlier native fixture used a different `rc` target
layout and consequently failed to cover this SDK behavior.

The new `prepare-runtime-link-map.py` validates the actual native all-target
recipe and EXEC before appending `all: override LDFLAGS += -Wl,-Map,...,--cref`.
It refuses drift, repeated preparation, existing output and unsafe make/linker
path syntax. The invocation remains before source/restart manifest capture.
Ordinary flags/libraries and the RC-only isolated build are preserved. The
map/relocation/provider verifier remains mandatory and unchanged.

The regression now uses the SDK's actual `all`/EXEC layout, reproduces the
old missing-map behavior, then executes the corrected strong selector from
a stripped native binary and verifies its real map/relocations. Existing
linker flags survive. The actual pinned SDK Makefile was separately accepted;
wrong target/EXEC fixtures refuse without mutation. Cached Makefile blob
a9193804cf819309bf287bcdb4fa6bd39de1c422 matches GitHub at SDKc25283e.

Host regression, pairing/staging checks and shell/Python syntax are separate
from pending new MIPS target verification. No target/firmware/RF acceptance
is inferred from this correction. Router unchanged.

## Independent pending GTK-timer work

Separate uncommitted ra2-rekey files implement/test counted admission and a
native periodic-callback wrapper.35 admission cases and both feature-guard
host modes passed, including a native closed-countdown key-write witness.
They are deliberately not wired into the candidate producer or CI in this
map-failure correction. Finish reviewing timer scheduling/lifetime and wire
the actual candidate before publishing that separate coherent package.
