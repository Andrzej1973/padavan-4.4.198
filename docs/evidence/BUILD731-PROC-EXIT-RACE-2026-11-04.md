# Standard 731: process disappears while the regression reads /proc

Run 41764591145 on source 7f15bb7 failed before fetch in the source retry
regression. Job 126359932241 reports ProcessLookupError (ESRCH) reading the
child's /proc stat file after exists() succeeded. The process had exited
during observation; this does not show a failed process-group kill.

Removed the exists/read race in the fixture. Direct read now treats ENOENT
and ESRCH as stopped; unrelated read errors remain failures. A deterministic
mock regression covers disappearance during read and preserves permission
errors. All ten tests, including real timeout/child termination and lock
ownership cases, passed. No production retry code change was needed.

Compared monitor 41764711812 artifact 13292560383 with the original log:
it identified the exact fixture, traceback and ESRCH. Its report was useful
for this early failure, so parser code was left unchanged. Later missing
EoIP/StrongSwan artifacts and downloads failure are consequences of the
early stop. No real source fetch or MIPS/WSC compilation ran in this build.
Temporary test directories were removed.
