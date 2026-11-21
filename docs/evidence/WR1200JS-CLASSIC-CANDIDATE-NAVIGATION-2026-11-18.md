# Reachable Classic IoT configuration in the isolated candidate

Optional1377 independently verified the configuration page and its script, but
the staging code installed no navigation link. A page reachable only by manually
entering its URL does not satisfy the intended Classic configuration workflow.

The isolated ROMFS stage now reuses `classic-navigation.js`, adding only its
loader to the existing Classic `www/state.js`. It validates the existing
single `show_banner` function and all four Main/Guest band shortcut anchors
before writing any payload. Changed/missing/aliased inputs and duplicate assets
refuse before mutation. Original state.js bytes remain an unchanged prefix;
existing file modes, Main/Guest buttons and unrelated entries are preserved.
The reused navigation asset supplies IoT banner/sidebar links and paired radio
tabs. Navigation itself never reads or saves configuration.

The four candidate assets are the IoT ASP page, configuration JS, navigation JS
and appended state.js. Their hashes are recorded in the staging manifest. The
post-build gate requires exactly those four entries plus explicit navigation
staging and rechecks their hashes after complete TRX/ROMFS comparison.
This remains candidate-only; the standard image and paused Modern UI are not
promoted by this change. No runtime activation control is added.

Host staging and existing 14-route DOM checks passed with synthetic inputs and
the actual pinned SDK Classic state.js from
`vipshmily/padavan-4.4@c25283e915a2a00a763774dd255b14aff997285e`.
Its SHA256 is
`2f3e2c7b82cb6ffbcfde8b4755fcafdfbd2059de2b20258cd5f65a176244f1be`.
The ABI edit/view suite now receives that same native file from its existing
sparse checkout. The complete combined edit/view suite passed with these
native inputs and the HTTP-to-RC composition extension; shell syntax, workflow
YAML and whitespace checks also passed. Exact-source target/image results
remain required. Simulated DOM checks do not establish browser
rendering or physical router acceptance.
