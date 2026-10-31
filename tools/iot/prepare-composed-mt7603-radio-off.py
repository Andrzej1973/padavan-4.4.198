#!/usr/bin/env python3
"""Add reviewed MT7603 checked radio-off to a separate partial queue bundle."""

import argparse
import ast
import hashlib
import json
import shutil
from pathlib import Path


def replace_once(source: str, old: str, new: str, label: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"{label}: changed anchor ({source.count(old)} matches)")
    return source.replace(old, new, 1)


def checked_off_source(here: Path) -> str:
    tree = ast.parse((here / "prepare-mt7603-checked-off-candidate.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "CHECKED_OFF"
                for target in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError("reviewed checked-off function is missing")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source, output = args.source.resolve(strict=True), args.output.resolve()
    if output.exists() or source == output or source in output.parents or output in source.parents:
        parser.error("output must be a new separate directory")
    parent_manifest = source.parent / (source.name + "-composition.json")
    manifest = json.loads(parent_manifest.read_text(encoding="utf-8"))
    if manifest.get("production_installed") is not False or manifest.get("complete_driver_tree") is not False:
        parser.error("input must be the reviewed partial bundle")
    for entry in manifest["files"]:
        path = source / entry["path"]
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            parser.error("input changed: " + entry["path"])

    names = ("include/radio-transition.h", "include/rtmp.h",
             "hw_ctrl/cmm_asic_mt.c", "common/rtmp_init_inf.c")
    data = {name: (source / name).read_text(encoding="utf-8") for name in names}
    radio = data[names[0]]
    radio = replace_once(radio,
        "joined_workers,shutdown_stage,close_notified,virtual_down_stage,virtual_up_stage;",
        "joined_workers,shutdown_stage,close_notified,virtual_down_stage,virtual_up_stage,mt_radio_off_stage;", names[0])
    radio = replace_once(radio,
        "s->shutdown_stage=0;s->close_notified=0;s->virtual_down_stage=0;",
        "s->shutdown_stage=0;s->close_notified=0;s->mt_radio_off_stage=0;s->virtual_down_stage=0;", names[0])
    radio = replace_once(radio,
        "s->joined_workers=0;s->shutdown_stage=0;s->close_notified=0;}",
        "s->joined_workers=0;s->shutdown_stage=0;s->close_notified=0;s->mt_radio_off_stage=0;}", names[0])
    data[names[0]] = radio
    data[names[1]] = replace_once(data[names[1]],
        "INT wr_iot_mgmt_exit_checked(RTMP_ADAPTER *pAd, const struct wr_iot_radio_ticket *ticket);",
        "INT wr_iot_mgmt_exit_checked(RTMP_ADAPTER *pAd, const struct wr_iot_radio_ticket *ticket);\n"
        "#ifdef RTMP_PCI_SUPPORT\n"
        "BOOLEAN wr_iot_mt_poll_txrx_empty(RTMP_ADAPTER *pAd);\n"
        "BOOLEAN wr_iot_mt_radio_off_checked(RTMP_ADAPTER *pAd, const struct wr_iot_radio_ticket *ticket);\n"
        "#endif", names[1])
    checked_off = checked_off_source(Path(__file__).resolve().parent)
    if checked_off.count("BOOLEAN wr_iot_mt_radio_off_checked(") != 1:
        raise ValueError("reviewed radio-off body changed")
    data[names[2]] = replace_once(data[names[2]],
        "}\n#endif\n\n\n#ifdef RTMP_SDIO_SUPPORT\nVOID MTSdioMlmeRadioOff",
        "}\n\n" + checked_off + "#endif\n\n\n#ifdef RTMP_SDIO_SUPPORT\nVOID MTSdioMlmeRadioOff", names[2])

    close = data[names[3]]
    start = close.index("INT wr_iot_drv_close_checked(")
    legacy, checked = close[:start], close[start:]
    if legacy.count("brc = RT28xxPciAsicRadioOff(pAd, RTMP_HALT, 0);") != 1:
        raise ValueError("legacy radio-off path changed")
    legacy_wait = '\tfor (i = 0 ; i < NUM_OF_TX_RING; i++)\n\t{\n\t\twhile (pAd->DeQueueRunning[i] == TRUE)\n\t\t{\n\t\t\tDBGPRINT(RT_DEBUG_TRACE, ("Waiting for TxQueue[%d] done..........\\n", i));\n\t\t\tRtmpusecDelay(1000);\n\t\t}\n\t}'
    bounded_wait = '\tfor (i = 0 ; i < NUM_OF_TX_RING; i++)\n\t{\n\t\tUINT32 wr_iot_dequeue_polls = 0;\n\t\twhile (pAd->DeQueueRunning[i] == TRUE)\n\t\t{\n\t\t\tif (wr_iot_dequeue_polls++ >= 1000U) {\n\t\t\t\tRTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);\n\t\t\t\tpAd->wr_iot_transition.shutdown_stage=3U;\n\t\t\t\tRTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);\n\t\t\t\treturn NDIS_STATUS_FAILURE;\n\t\t\t}\n\t\t\tDBGPRINT(RT_DEBUG_TRACE, ("Waiting for TxQueue[%d] done..........\\n", i));\n\t\t\tRtmpusecDelay(1000);\n\t\t}\n\t}'
    if checked.count(legacy_wait) == 1:
        checked = replace_once(checked, legacy_wait, '\tfor (i = 0 ; i < NUM_OF_TX_RING; i++)\n\t{\n\t\tunsigned int waited = 0;\n\t\twhile (pAd->DeQueueRunning[i] == TRUE)\n\t\t{\n\t\t\tif (waited++ >= 1000U) {\n\t\t\t\tRTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);\n\t\t\t\tpAd->wr_iot_transition.shutdown_stage = 3U;\n\t\t\t\tRTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);\n\t\t\t\treturn NDIS_STATUS_FAILURE;\n\t\t\t}\n\t\t\tDBGPRINT(RT_DEBUG_TRACE, ("Waiting for TxQueue[%d] done..........\\n", i));\n\t\t\tRtmpusecDelay(1000);\n\t\t}\n\t}', names[3])
    elif checked.count(bounded_wait) != 1:
        raise ValueError("checked close wait is neither reviewed legacy nor bounded form")
    checked = replace_once(checked,
        " if (stage > 2U) return NDIS_STATUS_FAILURE;\n if (stage == 2U) return NDIS_STATUS_SUCCESS;",
        " if (stage > 2U && stage != 4U) return NDIS_STATUS_FAILURE;\n"
        " if (stage == 2U) return NDIS_STATUS_SUCCESS;\n"
        "#if defined(RTMP_MAC_PCI) && defined(RTMP_PCI_SUPPORT)\n"
        " if (stage == 4U) {\n"
        "  if (pAd->chipCap.hif_type != HIF_MT ||\n"
        "      (pAd->infType != RTMP_DEV_INF_PCI &&\n"
        "       pAd->infType != RTMP_DEV_INF_PCIE)) return NDIS_STATUS_FAILURE;\n"
        "  goto wr_iot_mt_radio_off_resume;\n"
        " }\n#else\n if (stage == 4U) return NDIS_STATUS_FAILURE;\n#endif", names[3])
    anchor = "\t\tif (pAd->infType == RTMP_DEV_INF_PCI || pAd->infType == RTMP_DEV_INF_PCIE)\n\t\t{\n\t\t\tBOOLEAN brc = TRUE;"
    checked = replace_once(checked, anchor,
        "wr_iot_mt_radio_off_resume:\n" + anchor + "\n"
        "\t\t\tif (pAd->chipCap.hif_type == HIF_MT) {\n"
        "\t\t\t\tRTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);\n"
        "\t\t\t\tpAd->wr_iot_transition.shutdown_stage=4U;\n"
        "\t\t\t\tRTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);\n"
        "\t\t\t}", names[3])
    checked = replace_once(checked,
        "brc = RT28xxPciAsicRadioOff(pAd, RTMP_HALT, 0);",
        "brc = (pAd->chipCap.hif_type == HIF_MT) ?\n"
        "    wr_iot_mt_radio_off_checked(pAd, ticket) :\n"
        "    RT28xxPciAsicRadioOff(pAd, RTMP_HALT, 0);", names[3])
    checked = replace_once(checked,
        'DBGPRINT(RT_DEBUG_ERROR,("%s call RT28xxPciAsicRadioOff fail !!\\n", __FUNCTION__));\n\t\t\t\tRTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);\n\t\t\t\tpAd->wr_iot_transition.shutdown_stage=3U;',
        'DBGPRINT(RT_DEBUG_ERROR,("%s call RT28xxPciAsicRadioOff fail !!\\n", __FUNCTION__));\n\t\t\t\tRTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);\n\t\t\t\tif (pAd->chipCap.hif_type != HIF_MT)\n\t\t\t\tpAd->wr_iot_transition.shutdown_stage=3U;', names[3])
    data[names[3]] = legacy + checked

    shutil.copytree(source, output)
    for name, value in data.items():
        (output / name).write_text(value, encoding="utf-8", newline="\n")
    for entry in manifest["files"]:
        if entry["path"] in data:
            entry["stage"] += "+mt7603-radio-off"
            entry["sha256"] = hashlib.sha256((output / entry["path"]).read_bytes()).hexdigest()
    manifest["mt7603_checked_radio_off_composed"] = True
    manifest["physical_rf_observation_proven"] = False
    manifest["complete_driver_tree"] = False
    manifest["production_installed"] = False
    report = output.parent / (output.name + "-composition.json")
    report.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("PASS isolated MT7603 radio-off composition; release and runtime gates remain open")


if __name__ == "__main__":
    main()
