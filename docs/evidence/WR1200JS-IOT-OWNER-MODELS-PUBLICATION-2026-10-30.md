# Experimental peer ownership models — publication scope

Published source is limited to `tools/iot/peer-table-owner.h`,
`peer-open-owner.h` and their two standalone `check-peer-*-owner.c` tests.
These helpers model table reservations, balanced synchronous transactions,
closed-table admission, explicit reopen, startup insertion leases, stale
tickets and retained failures. They do not bind a production driver path.

On 2026-10-30 both tests compiled and executed successfully on Windows using
`C:\mingw64\bin\gcc.exe -std=c11 -O2 -Wall -Wextra -Werror -I tools/iot`.
Compile each test to a separate temporary executable, then run it. A zero
exit status is required for both compilation and execution.

This is host model evidence only: no real kernel locking, DMA retirement,
target ABI, firmware image or router runtime has been verified by these tests.
Callers must supply the documented shared lock and lifetime guarantees.
The unfinished close-table binding (candidate51), source preparers, CI edits,
vendor scratch trees and build artifacts remain local and are not part of
this publication. The last local documented full composition is candidate49;
candidate50b has admission-seam checks but no fresh full replay. Candidate51
still needs complete close-path fixtures and adapter-release review.

Sol remains the sole writer. Continue IoT before Zapret2/Modern acceptance.
Other modified and untracked files are preserved; this publication does not
certify them or mark IoT complete. No router changes or manual build dispatch.
