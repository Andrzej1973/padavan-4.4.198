# WR1200JS read-only WebUI audit — 2026-11-22

The router displayed firmware 4.4.198.9-1499_4b31ee6b. No settings were submitted.

## Live navigation

Opened Classic VPN server directly, plus 18 visible destinations: IoT,
firmware upgrade, network map, traffic, system information, advanced settings,
Wi-Fi 2.4 and 5 GHz, LAN, WAN, firewall, USB, administration, tweaks, wireless
status, system log, Shadowsocks and ZeroTier. Each rendered its page title.
The separately observed VPN client page rendered its WG/AWG profile selector.
The server page rendered WG/AWG selection and reported an active AmneziaWG peer.

Opened Modern home and all 12 sidebar sections. The IoT sidebar route showed
a development placeholder while the Wi-Fi IoT tab exposed the actual form.
The QoS section offered the Classic SQM page on this SQM-excluded image.
LAN and firewall used different destinations than the corresponding Classic
navigation. Modern VPN lacked a server link. Opening pages does not test
every nested tab, settings submission, service or recovery path.

## Local corrections and open defects

- Classic IoT initialization threw in show_loading_obj. Local page template
  now supplies the Classic banner/loading elements.
- Modern IoT sidebar now opens the same Wi-Fi IoT view as the top shortcut.
  Its read action still failed on the live build. Backend cause unresolved.
- Added the existing VPN server route to Classic services, ZeroTier tabs and
  Modern VPN metadata. No new VPN configuration path.
- Aligned Modern LAN/firewall links with the observed Classic routes.
  Modern QoS metadata only links the SQM control when selected by the build.
- The boot log reports Band Steering restart failure and retained MT7603
  recovery ownership; ra0 was observed down separately. Also observed DDNS
  server refusal, local DNS recursion refusal, HNAT drop messages and a Chinese
  automatic Internet-check message. Their causes and fixes remain open.

Local source and host checks are separate from a rebuilt TRX and on-device
acceptance. No router configuration or firmware changed during this audit.

## Band Steering restart diagnosis

The firmware log's state=4 maps to WR_APPLY_START_ERROR. In the native
lifecycle this is the failure to initialize both radios or verify service
start. off_confirmed=1 is a steering-off verification and does not establish
that Main was restored. The log also records a retained MT7603 Main recovery
owner after ra0 left br0. The installed 2.4 GHz entry can return to the
Band Steering callback while an owned asynchronous restart is still active.
That callback restarts both bands and immediately samples interface state;
this control-flow mismatch must be distinguished from the driver's retained
recovery closure. Runtime evidence does not yet identify the refused recovery
predicate. Do not bypass OFF/ownership checks or report the restart fixed.
The exact Chinese log text was absent from tracked overlay/tools sources.

## Recovery callback verification

The reaper now joins the accepted Main recovery work without canceling it.
The RTNL acquisition remains nonblocking. The host fixture covers a pending
callback reaching its RTNL refusal path, retry scheduling and exact netdev
reference release. A fresh candidate generated from the existing v22 input
passed v23b and v24c preparation and the PCI drain verifier (69 file hashes
and retire/drain/stop/join ordering). The v25b beacon and generation
preparations also succeeded. This isolated source verification does not
establish target compilation or reproduce the device failure.

The paired RC restart entry has distinct native, owned and refused results.
Its void wrapper returns for both owned and refused, so the Band Steering
callback cannot distinguish a queued restart from refusal by sampling an
interface flag. An owned restart needs an RC continuation driven by its
terminal result before the steering daemon starts. A refused restart must
remain an error without a second physical restart attempt.

## IoT read troubleshooting

Classic now explicitly sends the form media type required by the native IoT
POST readers. Modern uses that same value from the shared controller.
Both interfaces distinguish an unreadable token, a rejected view request,
an unavailable or busy RC service, and an invalid view response.
RC startup logs which registration failed, either the configuration backend
or the read endpoint. A failure leaves the rest of router startup available.
The logged messages carry no configuration or credential values.
The board-specific startup fixture covers successful registration, both
failure paths and optional boot arming. The deployed read failure remains
unclassified until the firmware and its actual RC state are checked.

## Manual 2.4 GHz OFF/ON on installed #1499

The owner applied OFF and ON in Classic. Read-only snapshots confirmed
rt_radio_x changed 1 -> 0 -> 1. mlme_radio_rt remained 1 throughout.
ra0, ra1 and ra2 remained down with zero RX/TX. rai0 remained UP/RUNNING
and traffic counters advanced. The filtered startup log showed no new
MT7603/Band Steering entries. After ON, iwpriv ra0 stat still reported
no private ioctls. The test proves saved intent changed without recovery
of the 2.4 GHz interface. It does not establish whether RC dispatched,
deferred or refused either event.

### Bridge membership after the OFF/ON cycle

The fixed read-only bridge check found ra0 still configured as a port of
br0, alongside eth2 and rai0. It found no bridge membership for ra1 or ra2.
The earlier kernel message reports a disabled bridge port and does not by
itself imply removal from the bridge. This snapshot rules out current
ra2 bridge membership as the observed stuck state. It cannot establish
earlier membership or whether an internal MT7603 owner still retains
resources associated with ra2.

### Shared MT7603 ownership hypothesis

The IoT bridge attach path admits only the owned br-iot bridge and refuses
a foreign master. The driver recovery admission is independent of bridge
membership. In the acquired-open recovery path, a non-idle auxiliary slot
in CLOSING blocks Main recovery even if the vendor reference count still
equals the number of interfaces. An idle auxiliary slot also blocks this
path if the vendor count still includes an unmatched reference. The host
fixture covers both cases and checks that admission resumes when the
registry and vendor count agree. These are code-level conditions, not
observed ra2 state on the installed image.

### Reboot comparison pending

Before the planned reboot, at 17:33:46 the router reported 2h11m uptime.
After tunnel availability was confirmed, it reported 2h13m at 17:35:25
and 2h14m at 17:36:22. The same startup log remained and 5 GHz counters
continued to increase. These captures belong to the same boot. In
particular, the earlier bridge forwarding record confirms Linux bridge
state only. First beacon transmission and client association on ra0
during a fresh boot still require evidence.

### SSH reboot result

The owner authorized a standard SSH reboot. The command returned zero,
and all ten subsequent uptime probes succeeded without an uptime reset.
At 17:38:39 the router reported 2h16m. This confirms the reboot had not
occurred during the observation window. The RC normal shutdown code can
defer reboot while a radio owner drains or retain the shutdown when
physical OFF fails. The available live evidence does not identify which,
if either, happened. No forced reboot was issued.

### Host verification after WSL restart

The MT7603 Main recovery reaper and owner fixtures, RC scheduler composition,
PID1 normal shutdown controller, and diagnostic candidate pairing passed.
The owner fixture exercises an in-progress auxiliary CLOSE and a vendor
reference count that does not match the registry. The RC scheduler fixture
holds fresh mailbox dispatch while normal shutdown is pending and resumes
dispatch after that condition clears. These are host checks. Target image
and router acceptance remain pending.
