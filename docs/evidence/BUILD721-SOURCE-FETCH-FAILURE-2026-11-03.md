# Build 721: source fetch timeout and stale shallow lock

Run 41708304141, revision ffa4e2eec21b93907d6be2bd9ddbec6b22d40537,
failed at Fetch pinned Padavan 4.4.198 source before compilation. Monitor
41711177928, artifact 13268150311 (agent-build-error-41711177928), identified
the correct run/job/step and early EOF followed by shallow.lock conflicts.
Compared it with original job 126175263665 logs: first failure appeared at
the 300-second attempt boundary; retries 2/3 then failed on the existing
shallow.lock. Missing EoIP/StrongSwan diagnostics and downloads failure were
downstream consequences. Monitor was useful; parser left unchanged.

The old subprocess.run timeout kills the Git parent without ensuring that
transport/index-pack descendants stop. Retry now starts an owned POSIX
process group, terminates the whole group on timeout, escalates and reaps
the parent. Only a newly created regular shallow.lock in the workflow's
exclusive padavan-4.4/amnezia-source repo may be removed after timeout.
Pre-existing locks, symlinks and the shared project checkout are preserved.
Padavan fetch timeout is now explicitly 900 seconds; checkout stays at 300.
Timeout is logged explicitly and retry count remains bounded at three.

Eight tests pass, including a real child that ignores SIGTERM, exact owned
lock cleanup, preservation of existing regular/symlink locks, configured
timeout, transient errors, persistent timeouts and intact argv. No network
or real source transfer was needed. Test fixture directories were removed.
The regression suite runs before source fetch in the workflow.

This is a local fix, not a successful rerun of build 721. No firmware or
IoT change and no router operation. Main project goal remains paused.
