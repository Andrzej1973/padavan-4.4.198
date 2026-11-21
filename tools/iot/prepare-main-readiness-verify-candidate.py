#!/usr/bin/env python3
"""Bind a bounded MT7603 main-radio VERIFY producer in a new isolated tree.

This is a source candidate only. It deliberately does not bind the result into
the production tree or solve the retained-open recovery/PCI-release gates.
"""

import argparse
import hashlib
import json
import shutil
from pathlib import Path


VERIFY_HELPER = r'''/* The caller is MainVirtualIF_open under RTNL with its module/netdev
 * owner held. Do not hold the transition spinlock across the BcnRingLock
 * observer; VERIFY admission fences participating radio/count mutations. */
static int wr_iot_main_readiness_verify(PRTMP_ADAPTER adapter,
 PNET_DEV main_dev,unsigned long generation)
{
 struct wr_iot_radio_ticket ticket;
 struct wr_iot_interface_ref *record;
 unsigned long flags;
 UINT vendor_count;
 int admitted=0,observed,verified=0;

 if (!adapter||!main_dev||!generation||main_dev!=adapter->net_dev)
  return 0;
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 vendor_count=VIRTUAL_IF_NUM(adapter);
 record=wr_iot_registry_find_owned(adapter->wr_iot_interface_refs,
                                   WDEV_NUM_MAX+1,main_dev);
 if (record&&record->generation==generation&&
     record->family==WR_REF_FAMILY_MAIN&&!record->removing&&
     vendor_count!=(UINT)~0U&&vendor_count&&
     wr_iot_registry_count_matches(adapter->wr_iot_interface_refs,
                                   WDEV_NUM_MAX+1,vendor_count))
  admitted=wr_iot_radio_begin(&adapter->wr_iot_transition,
   adapter->wr_iot_transition.epoch,WR_RADIO_VERIFY,&ticket);
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 if (!admitted)
  return 0;

 observed=wr_iot_mt7603_main_config_observed(adapter);

 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 record=wr_iot_registry_find_owned(adapter->wr_iot_interface_refs,
                                   WDEV_NUM_MAX+1,main_dev);
 if (record&&record->generation==generation&&
     record->family==WR_REF_FAMILY_MAIN&&!record->removing)
  verified=wr_iot_main_radio_verify_owned(&adapter->wr_iot_transition,
   adapter->wr_iot_interface_refs,WDEV_NUM_MAX+1,main_dev,
   VIRTUAL_IF_NUM(adapter),&ticket,observed);
 if (!verified&&adapter->wr_iot_transition.busy==WR_RADIO_VERIFY&&
     adapter->wr_iot_transition.serial==ticket.serial)
  wr_iot_radio_finish(&adapter->wr_iot_transition,&ticket,0);
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 wake_up_all(&adapter->wr_iot_ticket_wait);
 return verified;
}
'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    output = args.output.resolve()
    if output.exists() or output == source or source in output.parents or output in source.parents:
        parser.error("output must be a new isolated directory")

    main_file = source / "os/linux/rt_main_dev.c"
    body = main_file.read_bytes()
    signature = b"int MainVirtualIF_open(struct net_device *net_dev)"
    if body.count(signature) != 1:
        parser.error("expected exactly one reviewed MainVirtualIF_open")
    if (b"wr_iot_radio_finish_unverified" not in body or
            b"wr_iot_main_open_accepted" not in body or
            b"wr_iot_main_readiness_verify" in body):
        parser.error("main-open source differs from the reviewed unverified-owner base")
    required = (source / "include/mt7603-main-observe.h",
                source / "include/virtual-open-claim.h",
                source / "include/wr-iot-mbss-open-admission.inc")
    if not all(path.is_file() for path in required):
        parser.error("source lacks the reviewed MT7603 observer/MBSS admission")

    source_text = body.decode("utf-8")
    helper_anchor = '#include "virtual-open-claim.h"\n'
    if source_text.count(helper_anchor) == 1:
        source_text = source_text.replace(
            helper_anchor,
            helper_anchor + '#include "mt7603-main-observe.h"\n', 1)
    elif source_text.count(helper_anchor) == 0 and source_text.count('#include "rt_os_net.h"\n') == 1:
        # Later compositions keep the claim helpers in a shared header but
        # still need explicit declarations before the main-open producer.
        source_text = source_text.replace(
            '#include "rt_os_net.h"\n',
            '#include "rt_os_net.h"\n#include "virtual-open-claim.h"\n'
            '#include "mt7603-main-observe.h"\n', 1)
    else:
        parser.error("cannot place VERIFY helper after the shared claim helpers")
    signature_text = "int MainVirtualIF_open(struct net_device *net_dev)"
    source_text = source_text.replace(signature_text,
        VERIFY_HELPER + "\n" + signature_text, 1)

    fail_anchor = " if (!owned || !finished) return -1; /* retain pin; hardware may be open */"
    if source_text.count(fail_anchor) != 1:
        parser.error("main-open success gate changed; inspect before updating")
    source_text = source_text.replace(fail_anchor,
        fail_anchor + '''
 if (IS_MT7603(adapter)&&
     !wr_iot_main_readiness_verify(adapter,net_dev,generation)) {
  /* VERIFY failure leaves main_ready false and retains this acquired owner.
   * No secondary BSS may open; a recovery owner is still required before
   * this candidate can be bound to production or PCI removal. */
  DBGPRINT(RT_DEBUG_ERROR,
   ("MT7603 main radio readiness unverified; keeping secondary BSS closed\\n"));
  return -1;
 }''', 1)

    shutil.copytree(source, output)
    (output / "os/linux/rt_main_dev.c").write_text(
        source_text, encoding="utf-8", newline="\n")
    digest = hashlib.sha256((output / "os/linux/rt_main_dev.c").read_bytes()).hexdigest()
    manifest = {
        "source": str(source),
        "candidate": str(output),
        "production_installed": False,
        "main_readiness_verify_bound": True,
        "recovery_owner_bound": False,
        "pci_release_gate_bound": False,
        "rt_main_dev_sha256": digest,
    }
    Path(str(output) + ".manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("Prepared isolated MT7603 main-readiness VERIFY candidate")
    print("Recovery owner and PCI release remain unbound; do not package")


if __name__ == "__main__":
    main()
