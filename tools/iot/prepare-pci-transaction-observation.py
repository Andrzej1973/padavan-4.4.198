#!/usr/bin/env python3
"""Stage real PCI config-space reads in a separate nonproduction MT7603 tree."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError("PCI observation insertion anchor changed")
    return text.replace(old, new, 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source, output = args.source.resolve(strict=True), args.output.resolve()
    if output.exists() or source == output or source in output.parents or output in source.parents:
        parser.error("output must be new and separate")
    manifest = json.loads((source.parent / (source.name + "-composition.json")).read_text(encoding="utf-8"))
    if manifest.get("production_installed") is not False or \
            manifest.get("pci_remove_two_work_joins_staged") is not True or \
            manifest.get("pci_release_gate_bound") is not False:
        parser.error("source is not the reviewed partial PCI-join candidate")
    for record in manifest["files"]:
        path = source / record["path"]
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
            parser.error("source changed: " + record["path"])
    name = "os/linux/pci_main_dev.c"
    text = (source / name).read_text(encoding="utf-8")
    text = once(text, "#include <linux/pci.h>",
                "#include <linux/pci.h>\n#include <linux/delay.h>\n"
                "#include \"pci-transaction-observer.h\"")
    signature = "static VOID DEVEXIT rt_pci_remove(struct pci_dev *pci_dev)"
    wrappers = """static int wr_iot_pci_clear_master(void *context)
{
 pci_clear_master((struct pci_dev *)context);
 return 0; /* Observer separately verifies the config-space readback. */
}
static int wr_iot_pci_read_word(void *context, unsigned int offset,
                                unsigned short *value)
{
 return pci_read_config_word((struct pci_dev *)context, offset, value);
}
static void wr_iot_pci_sleep_ms(void *context, unsigned int milliseconds)
{
 (void)context;
 msleep(milliseconds);
}

"""
    text = once(text, signature, wrappers + signature)
    old = "\t\t/* Free RTMP_ADAPTER related structures. */\n\t\tRtmpRaDevCtrlExit(pAd);"
    observation = """\t\t/* PCI reads are meaningful only after the checked physical stop.
\t\t * They are necessary, not proof that all callbacks/DMA are quiescent. */
\t\t{
\t\t\tstruct wr_iot_pci_transaction_io io = {
\t\t\t\tpci_dev, wr_iot_pci_clear_master,
\t\t\t\twr_iot_pci_read_word, wr_iot_pci_sleep_ms
\t\t\t};
\t\t\tunsigned long epoch;
\t\t\tint ready, capability;
\t\t\tenum wr_iot_pci_transaction_result observed;
\t\t\tRTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
\t\t\tready = adapter->wr_iot_transition.retiring &&
\t\t\t adapter->wr_iot_transition.phase == WR_RADIO_DOWN &&
\t\t\t !adapter->wr_iot_transition.busy &&
\t\t\t !adapter->wr_iot_transition.active_tx &&
\t\t\t !adapter->wr_iot_transition.reset_pending &&
\t\t\t adapter->wr_iot_transition.shutdown_stage == 2U &&
\t\t\t adapter->wr_iot_transition.mt_radio_off_stage == 4U &&
\t\t\t adapter->wr_iot_transition.virtual_down_stage == 2U;
\t\t\tepoch = adapter->wr_iot_transition.epoch;
\t\t\tRTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
\t\t\tif (!ready || !epoch)
\t\t\t\treturn;
\t\t\tcapability = pci_find_capability(pci_dev, PCI_CAP_ID_EXP);
\t\t\tobserved = wr_iot_pci_disable_master_and_observe(&io, capability);
\t\t\tif (observed != WR_IOT_PCI_TX_CLEAR_OBSERVED)
\t\t\t\treturn;
\t\t\tRTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
\t\t\tready = adapter->wr_iot_transition.epoch == epoch &&
\t\t\t adapter->wr_iot_transition.retiring &&
\t\t\t adapter->wr_iot_transition.phase == WR_RADIO_DOWN &&
\t\t\t !adapter->wr_iot_transition.busy &&
\t\t\t !adapter->wr_iot_main_recovery.deferred_owners;
\t\t\tRTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
\t\t\tif (!ready)
\t\t\t\treturn;
\t\t}
\t\t/* Free RTMP_ADAPTER related structures. */
\t\tRtmpRaDevCtrlExit(pAd);"""
    text = once(text, old, observation)
    header_name = "include/pci-transaction-observer.h"
    header = Path(__file__).with_name("pci-transaction-observer.h").read_bytes()
    shutil.copytree(source, output)
    (output / name).write_text(text, encoding="utf-8", newline="\n")
    (output / header_name).write_bytes(header)
    for record in manifest["files"]:
        if record["path"] == name:
            record["stage"] += "+pci-config-observation"
            record["sha256"] = hashlib.sha256((output / name).read_bytes()).hexdigest()
    manifest["files"].append({"path": header_name, "stage": "pci-config-observation",
                              "sha256": hashlib.sha256(header).hexdigest()})
    manifest["pci_config_observer_staged"] = True
    manifest["pci_release_gate_bound"] = False
    manifest["complete_driver_tree"] = False
    manifest["production_installed"] = False
    (output.parent / (output.name + "-composition.json")).write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("PASS partial PCI observation; full release proof still unbound")


if __name__ == "__main__":
    main()
