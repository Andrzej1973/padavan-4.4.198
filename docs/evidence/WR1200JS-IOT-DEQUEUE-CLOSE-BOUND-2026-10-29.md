# Candidate dequeue close bound

The final-source checked-close host fixture hung because the candidate
copied the vendor's unbounded `while (DeQueueRunning[i] == TRUE)` loop.
Its existing timeout case deliberately leaves that flag set. The delay stub
only increments a counter, so the hang exposed missing candidate behavior.

`prepare-checked-close.py` now bounds each ring to 1000 delay polls. On
exhaustion it records shutdown uncertainty stage 3 under the transition lock
and returns failure before management-task join and later resource release.
A subsequent close does not treat that uncertainty as a fresh retry.
The original vendor close remains unchanged; this affects the isolated
checked candidate only. The nominal delays are not a wall-clock deadline:
scheduling and individual delay implementation still affect elapsed time.

Regenerated the complete source bundle into
`.iot-local-check/full-queue-20261029d`. Extracted final checked-close and
close-chain fixtures both compiled with GCC C11 `-Wall -Wextra -Werror -O2`
and exited 0. The former covers stuck dequeue, retained stage 3, no later
join/free and refused retry; the latter checks the injected outer close chain.
Injected workers/hardware do not establish target memory visibility,
MIPS compilation, bounded whole-driver shutdown or physical-device safety.

Still required: target compilation, caller/retention checks in full driver,
hardware TxS retirement proof and supervised device acceptance. No image
was built and no router state was changed.
