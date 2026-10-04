# Full driver build: WPS-disabled compatibility

Run 37192024927 built the normal WR1200JS firmware and passed image/config gates, then failed the isolated full Band Steering driver compilation. Compiler errors were unguarded PWSC_CTRL/WscControl references and IE_LISTS.bWscCapable in MT76x3 ap_band_steering.c. The corresponding structures/fields in the pinned source exist under WSC_AP_SUPPORT.

prepare-wps-guards.py requires the exact grant-prepared modern AP source hash and wraps only the WPS-specific connection block and association metadata reference in WSC_AP_SUPPORT. When WPS is absent, bWpsAssoc is explicitly FALSE. Existing WPS-enabled behavior is retained; no WPS config selector is enabled. Local preparation/repeat rejection checks passed; full SDK recompilation is requested, not yet proven.

The next full build includes the legacy main-BSS isolation candidate and an independent complete rc clone compilation after a successful normal firmware build. Full rc diagnostics run even if the isolated kernel probe fails, so both candidate components yield evidence; original candidate failures still fail the workflow. Neither candidate is installed in the normal firmware image. Router runtime, service ownership/lifecycle and WebUI remain pending.
