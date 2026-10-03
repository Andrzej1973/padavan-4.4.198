# WebUI / reboot / scheduled reboot audit

## Scope

This is a continuation of the Hadzhioglu -> nilabsent comparison, using the current `hadzhioglu/padavan-ng` tree as the reference and the `experimental/hadzhioglu-compare` branch as the working branch.

## 1. Normal router reboot from WebUI

The current nilabsent WebUI already has the normal reboot action. `state.js` defines `reboot()` and the backend exposes `sys_reboot()` in `trunk/user/httpd/web_ex.c`; therefore there is no missing standalone reboot component to transplant.

**Decision: do not copy an old Hadzhioglu reboot implementation.**

The important rule is to preserve the current nilabsent WebUI behavior while adding only genuinely missing functionality.

## 2. Scheduled reboot

A scheduled reboot is not a separate reboot daemon in current Hadzhioglu. The WebUI exposes the normal Cron daemon/scheduler configuration through `Advanced_Services_Content.asp`: `crond_enable` enables the scheduler and `crontab.login` is the editable crontab text area.

The same mechanism is already present in current nilabsent. The WebUI shows the Crond toggle and the `Scheduler tasks (Crontab)` editor when `crond_enable` is enabled.

A scheduled reboot is therefore simply a cron entry such as:

    00 06 * * */2 reboot

This is also how Padavan documentation/examples implement scheduled reboot: enable the Cron daemon and put the reboot command in the Crontab field. No additional C backend or special WebUI page is required.

**Decision: no scheduled-reboot code transplant.**

## 3. What this means for our branch

Do not add a new reboot scheduler UI merely because the feature is not a separate menu item. Doing so would diverge from Hadzhioglu rather than reproduce it.

The current experimental branch should retain:

- normal WebUI reboot;
- Cron daemon enable/disable;
- editable persistent `crontab.login`;
- ordinary `reboot` command usable from cron.

## 4. Related WebUI work that IS real

The VLMCSD transplant remains a genuine missing component. It adds the Hadzhioglu-style `KMS Activation server` switch to `Advanced_Services_Content.asp`, `vlmcsd_enable`, restart notification wiring, and the runtime package.

The branch also stages the current Hadzhioglu userspace packages `socat` and `ndisc6/rdisc6` because the WR1200JS configuration already has `CONFIG_FIRMWARE_INCLUDE_SOCAT=y` and `CONFIG_FIRMWARE_INCLUDE_NDISC6_RDISC6=y`.

These package integrations still require build verification before they are considered complete.

## 5. Next investigation

Continue with current-Hadzhioglu packages and WebUI features that are actually absent from nilabsent:

1. USB/IP userspace + sysfsutils (kernel side already exists in nilabsent).
2. socat build/runtime integration verification.
3. ndisc6/rdisc6 build/runtime integration verification.
4. obfs4 only after checking the MIPS/uClibc toolchain requirements.
5. radvd provenance before considering any transfer.

No feature should be imported merely because it has a different SHA or a different menu layout.
