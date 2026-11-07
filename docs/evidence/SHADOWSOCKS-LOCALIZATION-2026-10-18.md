# Shadowsocks page localization checkpoint — 2026-10-18

The user reported that the Shadowsocks settings page still displayed Chinese
labels. The available ROMFS snapshot `artifacts-410/romfs-selected/www/Shadowsocks.asp`
contained Chinese characters on 197 source lines, including navigation,
primary client settings, node management, advanced settings, rules, runtime
log and help text. This confirms the issue is in the page source, rather than
just a browser-language preference.

## Source changes

- Added `tools/prepare-shadowsocks-localization.py` to replace the page's main
  client navigation and primary settings captions/options, plus static node
  subscription actions and node-editor labels, with EN/UK/RU dictionary keys.
- Extended the transform to localize dynamic node actions (subscription
  updates, delete and ping progress/errors, confirmation, editor actions,
  import prompts/results, and missing node labels) in EN/UK/RU as well.
- Preserved option `value` attributes and router NVRAM fields. This step only
  changes displayed text.
- Added the transform to the WR1200JS source preparation workflow.
- Added a final-ROMFS CI gate that rejects remaining CJK text in the page and
  checks every added translation against the exact EN/UK/RU dictionary value.
- Updated `docs/PROJECT-DELIVERY-SCOPE.md` to retain the remaining translation
  work explicitly.

## Limits and evidence

The localization transform and final-image gate passed on an isolated fixture
assembled from the saved build #410 ROMFS page and dictionaries. The fixture
run found and corrected replacement-order drift in the subscription notice and
additional visible/hidden strings for the encryption label and refresh buttons.
It verifies every added EN/UK/RU value and rejects CJK characters in the page
outside HTML/JavaScript comments.

This fixture is not a new firmware build and does not prove the latest final
ROMFS or router browser behavior. No router state was changed. CI has not yet
run against a newly built image.

## Recheck of the remaining-Chinese note — 2026-10-18

The earlier statement that CJK text remained in the inherited dictionaries was
rechecked against the available `artifacts-410/romfs-selected/www/{EN,UK,RU}.dict`;
none of those three files contains a CJK character. The active WR1200JS profile
comments out `CONFIG_FIRMWARE_INCLUDE_SMARTDNS` and sets
`CONFIG_FIRMWARE_INCLUDE_SQM=n`, so those optional pages are not present in the
active service scope. This corrects the stale backlog note; it does not prove
localization of either optional page if later enabled, nor does it replace the
pending final-image and browser checks for the localized Shadowsocks page.

## Isolated recheck — 2026-10-18 18:07 UTC

Replayed the current source transform using a scratch copy of the saved build
#410 `Shadowsocks.asp` and its EN/UK/RU image dictionaries. The localized page
passed the current final-ROMFS verifier: no CJK remained outside comments and
all new dictionary values matched exactly. Scratch data was removed after the
check; the saved build artifact was not modified. This is repeatable source and
verifier evidence against the actual older page contents, not a new firmware
image, CI result or router-browser check. Current image integration and runtime
acceptance remain pending.

## GitHub workflow boundary — 2026-10-18

The current GitHub `main` at `d1dc0ebaf82af316ad8ba65a01952c229c69e919`
(build #478) does not contain either the source-preparation invocation or the
final-ROMFS invocation of `prepare-shadowsocks-localization.py`. Both steps are
present in the local uncommitted workflow. Therefore build #478 is not CI/image
evidence for this localization change. A subsequent committed build must run
both steps successfully before claiming the translated page is in a firmware
image.
