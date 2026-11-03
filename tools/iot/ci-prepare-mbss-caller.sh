#!/usr/bin/env bash
# Run from repository root. Input is the raw-recovery-free-fenced candidate.
set -euo pipefail
merged=$1
candidate=$2
results=$3
for layer in mbss-work-binding mbss-external-join mbss-pci-drain \
  mbss-pci-stop mbss-reaper-gate mbss-submission-entry; do
  python3 "tools/iot/prepare-$layer.py" "$merged" "$candidate/$layer"
  merged="$candidate/$layer"
done
python3 tools/iot/check-mbss-work-binding.py "$merged" --stop-join --submit
python3 tools/iot/prepare-mbss-poll-caller.py "$merged" "$candidate/mbss-poll-caller"
merged="$candidate/mbss-poll-caller"
gcc -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined -fno-pie -no-pie \
  -DWR_IOT_INSTALLED_POLL -I"$merged/include" -Itools/iot \
  tools/iot/check-mbss-poll-caller.c -o "$results/check-installed-mbss-poll"
"$results/check-installed-mbss-poll"
gcc -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined -fno-pie -no-pie \
  -DWR_IOT_INSTALLED_HANDOFF -I"$merged/include" -Itools/iot \
  tools/iot/check-mbss-recovery-handoff.c -o "$results/check-installed-mbss-handoff"
"$results/check-installed-mbss-handoff"
cp "$merged.manifest.json" "$results/mbss-submission-candidate.json"
