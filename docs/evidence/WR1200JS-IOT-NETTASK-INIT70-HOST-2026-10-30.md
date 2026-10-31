# Network-task partial initialization70 — isolated candidate

Source review confirmed OS_ABL_FUNC_SUPPORT maps RTMP_OS_TASKLET_INIT to
BOOLEAN RtmpOsTaskletInit. Its allocation failure returns FALSE; the original
network init ignores it. RtmpOsTaskletKill tolerates NULL pContent, joins an
allocated task and clears it. Native init is void; the checked preparation
preserves that interface instead of testing a nonexistent return value.

prepare-nettask-init-unwind.py pins the exact69c predecessor and transforms
20 lexical init sites. Each successfully initialized task is recorded in a
bounded stack. Failure joins only those tasks in reverse order before releasing
the initialization reservation. Submission remains blocked; joined stays true.
A subsequent init can retry. A local pointer prevents repeated evaluation of
an index by the kill macro. The unsuccessful70c host run exposed that issue
(exit -1073741819); corrected70d passed. Earlier generated drafts are retained.

Verified strict GCC C11/O2/Wall/Wextra/Werror native base/extended Init/Exit
fixtures and OS_ABL base/extended allocation-failure fixtures. Each enabled
allocation site is failed in turn, then successful retry/exit is checked.
Extended flags: CONFIG_ANDES_SUPPORT, MT_MAC, CONFIG_ATE, UAPSD_SUPPORT,
CONFIG_AP_SUPPORT, DFS_SUPPORT. Previous69 report used ANDES_SUPPORT, which
was insufficient to activate rx1;69 was rerun with CONFIG_ANDES_SUPPORT and
passed. The source spelling is authoritative.

Kernel allocation, scheduling, lock and callback operations remain mocked.
This verifies extracted control flow, not actual OS_ABL binary ABI or kernel
concurrency. Other resource-allocation families and final PCI/child retirement
bindings remain open. Candidates67–70 remain isolated; composed chain ends64.
Next adapt composed fixtures and inspect whole caller unwind before target
validation. No firmware build, router changes, commit or push in this step.
