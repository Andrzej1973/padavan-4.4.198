#!/usr/bin/env python3
"""Stage pinned mt76x3 TxS metadata changes outside firmware sources.

Generation-tagged cancel is only for a packet proved not published to hardware.
This stage does not provide that caller or prove BSS retirement.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path


PINNED_BLOBS = {
    "tx_rx/txs.c": "ece66c6ef0263a07015783f620fb968d065fc36f",
    "include/mac/mac_mt/mt_mac.h": "30de2ef29743fda3c600e4e47448165ed24dc81e",
    "mac/mt_mac.c": "8aa1a977e043cb6060990dcc89a5ebe605af0918",
    "include/mac/mac.h": "0dd885ca5b1b08e84542e17e8418aa10177fee1e",
}


def git_blob(data: bytes) -> str:
    header = b"blob " + str(len(data)).encode("ascii") + b"\0"
    return hashlib.sha1(header + data).hexdigest()


def replace_once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError(f"Pinned TxS anchor changed: {old[:72]!r}")
    return text.replace(old, new, 1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path, help="exact pinned mt76x3 tree")
    parser.add_argument("output", type=Path, help="new, separate candidate directory")
    args = parser.parse_args()
    root, output = args.source.resolve(), args.output.resolve()
    if output.exists() or root == output or root in output.parents or output in root.parents:
        raise SystemExit("Output must be new and separate from the source")
    source = root / "tx_rx" / "txs.c"
    original = source.read_bytes()
    blob = git_blob(original)
    if blob != PINNED_BLOBS["tx_rx/txs.c"]:
        raise SystemExit(f"Wrong TxS source blob: {blob}")
    header_original = (root / "include/mac/mac_mt/mt_mac.h").read_bytes()
    header_blob = git_blob(header_original)
    if header_blob != PINNED_BLOBS["include/mac/mac_mt/mt_mac.h"]:
        raise SystemExit(f"Wrong TxS header blob: {header_blob}")
    header = replace_once(
        header_original.decode("utf-8"),
        "\tTXS_STATUS TxSStatus[TXS_STATUS_NUM];",
        "\tTXS_STATUS TxSStatus[TXS_STATUS_NUM];\n\tNDIS_SPIN_LOCK TxSStatusLock;\n\tUINT32 ReservationGeneration;",
    )
    header = replace_once(header, "\tUINT32 Priv;\n} TXS_STATUS, *PTXS_STATYS;",
                          "\tUINT32 Priv;\n\tUINT32 Generation;\n} TXS_STATUS, *PTXS_STATYS;")
    header = replace_once(
        header,
        "UINT8 AddTxSStatus(struct _RTMP_ADAPTER *pAd, UINT8 Type, UINT8 PktPid, UINT8 PktType,\n"
        "\t\t\t\t\t\tUINT8 PktSubType, UINT16 TxRate, UINT32 Priv);",
        "INT32 AddTxSStatus(struct _RTMP_ADAPTER *pAd, UINT8 Type, UINT8 PktPid, UINT8 PktType,\n"
        "\t\t\t\t\t\tUINT8 PktSubType, UINT16 TxRate, UINT32 Priv, UINT8 *OutPid, UINT32 *OutGeneration);\n"
        "INT32 CancelTxSReservation(struct _RTMP_ADAPTER *pAd, UINT8 Pid, UINT32 Generation);",
    )
    data = original.decode("utf-8")
    data = replace_once(
        data,
        "\t\t\tbss_idx = Priv;\n\t\t\tpMbss = &pAd->ApCfg.MBSSID[bss_idx];",
        "\t\t\tif (Priv >= pAd->ApCfg.BssidNum ||\n"
        "\t\t\t    Priv >= MAX_MBSSID_NUM(pAd))\n"
        "\t\t\t\treturn -1;\n"
        "\t\t\tbss_idx = (UCHAR)Priv;\n\t\t\tpMbss = &pAd->ApCfg.MBSSID[bss_idx];",
    )
    data = replace_once(
        data,
        "\t\t\tBSS_STRUCT *pMbss = NULL;\n\t\t\tif (Priv >= pAd->ApCfg.BssidNum ||",
        "\t\t\tBSS_STRUCT *pMbss = NULL;\n"
        "#if defined(RTMP_MAC_PCI) && defined(MT_MAC)\n\t\t\tULONG BcnFlags;\n"
        "\t\t\tRTMP_IRQ_LOCK(&pAd->BcnRingLock, BcnFlags);\n#endif\n"
        "\t\t\tif (Priv >= pAd->ApCfg.BssidNum ||",
    )
    data = replace_once(
        data,
        "\t\t\t    Priv >= MAX_MBSSID_NUM(pAd))\n\t\t\t\treturn -1;",
        "\t\t\t    Priv >= MAX_MBSSID_NUM(pAd)) {\n"
        "#if defined(RTMP_MAC_PCI) && defined(MT_MAC)\n\t\t\t\tRTMP_IRQ_UNLOCK(&pAd->BcnRingLock, BcnFlags);\n#endif\n"
        "\t\t\t\treturn -1;\n\t\t\t}\n"
        "\t\t\tif (pAd->ApCfg.MBSSID[Priv].bcn_buf.bcn_state == BCN_TX_STOP) {\n"
        "#if defined(RTMP_MAC_PCI) && defined(MT_MAC)\n\t\t\t\tRTMP_IRQ_UNLOCK(&pAd->BcnRingLock, BcnFlags);\n#endif\n"
        "\t\t\t\treturn -1;\n\t\t\t}",
    )
    data = replace_once(
        data,
        "\t\t\tif (pMbss->timer_loop >= MAX_TIME_RECORD)\n"
        "\t\t\t\tpMbss->timer_loop = 0;\n\n\t\t\treturn 0;",
        "\t\t\tif (pMbss->timer_loop >= MAX_TIME_RECORD)\n"
        "\t\t\t\tpMbss->timer_loop = 0;\n"
        "#if defined(RTMP_MAC_PCI) && defined(MT_MAC)\n\t\t\tRTMP_IRQ_UNLOCK(&pAd->BcnRingLock, BcnFlags);\n#endif\n\n"
        "\t\t\treturn 0;",
    )
    data = replace_once(
        data,
        "\tRemoveTxSStatus(pAd, Pid, &Type, &PktPid, &PktType, &PktSubType, &TxRate, &Priv);",
        "\tif (Pid >= TXS_STATUS_NUM ||\n"
        "\t    RemoveTxSStatus(pAd, (UINT8)Pid, &Type, &PktPid, &PktType,\n"
        "\t                       &PktSubType, &TxRate, &Priv) != 0)\n"
        "\t\treturn -1;",
    )
    data = replace_once(
        data,
        "\tTxSCtl->TxSStatus[TxSPid].State = TXS_UNUSED;\n\t\n"
        "\t*Type = TxSCtl->TxSStatus[TxSPid].Type;",
        "\tif (TxSCtl->TxSStatus[TxSPid].State != TXS_USED)\n"
        "\t\treturn -1;\n\t\n"
        "\t*Type = TxSCtl->TxSStatus[TxSPid].Type;",
    )
    data = replace_once(
        data,
        "\t*TxRate = TxSCtl->TxSStatus[TxSCtl->TxSPid].TxRate;",
        "\t*TxRate = TxSCtl->TxSStatus[TxSPid].TxRate;",
    )
    data = replace_once(
        data,
        "\t*TxSPriv = TxSCtl->TxSStatus[TxSPid].Priv;\n\n\treturn 0;",
        "\t*TxSPriv = TxSCtl->TxSStatus[TxSPid].Priv;\n"
        "\tTxSCtl->TxSStatus[TxSPid].State = TXS_UNUSED;\n\t\n\treturn 0;",
    )
    data = replace_once(
        data,
        "\tfor (Index = 0; Index < TXS_STATUS_NUM; Index++)",
        "\tNdisAllocateSpinLock(pAd, &TxSCtl->TxSStatusLock);\n\tfor (Index = 0; Index < TXS_STATUS_NUM; Index++)",
    )
    exit_start = data.index("INT32 ExitTxSTypeTable(RTMP_ADAPTER *pAd)")
    exit_end = data.index("\n}\n", exit_start) + 2
    exit_body = data[exit_start:exit_end]
    exit_body = replace_once(
        exit_body, "\treturn 0;", "\tNdisFreeSpinLock(&TxSCtl->TxSStatusLock);\n\treturn 0;"
    )
    data = data[:exit_start] + exit_body + data[exit_end:]
    add_start = data.index("UINT8 AddTxSStatus(RTMP_ADAPTER *pAd,")
    add_end = data.index("\n}\n", add_start) + 2
    add_body = data[add_start:add_end]
    add_body = replace_once(
        add_body,
        "UINT8 AddTxSStatus(RTMP_ADAPTER *pAd, UINT8 Type, UINT8 PktPid, UINT8 PktType,\n"
        "\t\t\t\t\t\tUINT8 PktSubType, UINT16 TxRate, UINT32 Priv)",
        "INT32 AddTxSStatus(RTMP_ADAPTER *pAd, UINT8 Type, UINT8 PktPid, UINT8 PktType,\n"
        "\t\t\t\t\t\tUINT8 PktSubType, UINT16 TxRate, UINT32 Priv, UINT8 *OutPid, UINT32 *OutGeneration)",
    )
    add_body = replace_once(
        add_body,
        "\tTXS_CTL *TxSCtl = &pAd->TxSCtl;\n\n"
        "\tif (TxSCtl->TxSStatus[TxSCtl->TxSPid].State == TXS_USED)\n"
        "\t{\n\t\tTxSCtl->TxSFailCount++;\n\t}\n",
        "\tTXS_CTL *TxSCtl = &pAd->TxSCtl;\n\tULONG Flags;\n"
        "\tUINT32 scan;\n\tUINT8 pid = 0;\n\n"
        "\tif (!OutPid || !OutGeneration)\n\t\treturn -1;\n"
        "\tRTMP_SPIN_LOCK_IRQSAVE(&TxSCtl->TxSStatusLock, &Flags);\n"
        "\tfor (scan = 0; scan < TXS_STATUS_NUM; scan++) {\n"
        "\t\tpid = (UINT8)(TxSCtl->TxSPid + scan);\n"
        "\t\tif (TxSCtl->TxSStatus[pid].State != TXS_USED)\n"
        "\t\t\tbreak;\n\t}\n"
        "\tif (scan == TXS_STATUS_NUM) {\n"
        "\t\tTxSCtl->TxSFailCount++;\n"
        "\t\tRTMP_SPIN_UNLOCK_IRQRESTORE(&TxSCtl->TxSStatusLock, &Flags);\n"
        "\t\treturn -1;\n\t}\n",
    )
    add_body = add_body.replace("TxSCtl->TxSStatus[TxSCtl->TxSPid]", "TxSCtl->TxSStatus[pid]")
    add_body = replace_once(
        add_body,
        "TxSCtl->TxSStatus[pid].TxSPid = TxSCtl->TxSPid;",
        "TxSCtl->TxSStatus[pid].TxSPid = pid;",
    )
    add_body = replace_once(
        add_body,
        "\tTxSCtl->TxSPid++;\n\t\n\treturn (TxSCtl->TxSPid - 1);",
        "\tTxSCtl->TxSPid = (UINT8)(pid + 1);\n"
        "\tTxSCtl->ReservationGeneration++;\n"
        "\tif (!TxSCtl->ReservationGeneration)\n\t\tTxSCtl->ReservationGeneration++;\n"
        "\tTxSCtl->TxSStatus[pid].Generation = TxSCtl->ReservationGeneration;\n"
        "\t*OutPid = pid;\n\t*OutGeneration = TxSCtl->ReservationGeneration;\n"
        "\tRTMP_SPIN_UNLOCK_IRQRESTORE(&TxSCtl->TxSStatusLock, &Flags);\n\t\n\treturn 0;",
    )
    data = data[:add_start] + add_body + data[add_end:]
    remove_start = data.index("INT32 RemoveTxSStatus(RTMP_ADAPTER *pAd,")
    remove_end = data.index("\n}\n", remove_start) + 2
    remove_body = data[remove_start:remove_end]
    remove_body = replace_once(
        remove_body,
        "\tTXS_CTL *TxSCtl = &pAd->TxSCtl;",
        "\tTXS_CTL *TxSCtl = &pAd->TxSCtl;\n\tULONG Flags;\n\n"
        "\tRTMP_SPIN_LOCK_IRQSAVE(&TxSCtl->TxSStatusLock, &Flags);",
    )
    remove_body = replace_once(
        remove_body,
        "\tif (TxSCtl->TxSStatus[TxSPid].State != TXS_USED)\n\t\treturn -1;",
        "\tif (TxSCtl->TxSStatus[TxSPid].State != TXS_USED) {\n"
        "\t\tRTMP_SPIN_UNLOCK_IRQRESTORE(&TxSCtl->TxSStatusLock, &Flags);\n"
        "\t\treturn -1;\n\t}",
    )
    remove_body = replace_once(
        remove_body,
        "\tTxSCtl->TxSStatus[TxSPid].State = TXS_UNUSED;\n\t\n\treturn 0;",
        "\tTxSCtl->TxSStatus[TxSPid].State = TXS_UNUSED;\n"
        "\tRTMP_SPIN_UNLOCK_IRQRESTORE(&TxSCtl->TxSStatusLock, &Flags);\n\t\n\treturn 0;",
    )
    data = data[:remove_start] + remove_body + data[remove_end:]
    cancel = '''\n\n/* Only call before this exact packet is published to hardware. */
INT32 CancelTxSReservation(RTMP_ADAPTER *pAd, UINT8 Pid, UINT32 Generation)
{
\tTXS_CTL *TxSCtl = &pAd->TxSCtl;
\tULONG Flags;
\tINT32 result = -1;

\tif (!Generation)
\t\treturn -1;
\tRTMP_SPIN_LOCK_IRQSAVE(&TxSCtl->TxSStatusLock, &Flags);
\tif (TxSCtl->TxSStatus[Pid].State == TXS_USED &&
\t    TxSCtl->TxSStatus[Pid].Generation == Generation) {
\t\tTxSCtl->TxSStatus[Pid].State = TXS_UNUSED;
\t\tresult = 0;
\t}
\tRTMP_SPIN_UNLOCK_IRQRESTORE(&TxSCtl->TxSStatusLock, &Flags);
\treturn result;
}'''
    data = data[:remove_start + len(remove_body)] + cancel + data[remove_start + len(remove_body):]
    mac_original = (root / "mac/mt_mac.c").read_bytes()
    mac_blob = git_blob(mac_original)
    if mac_blob != PINNED_BLOBS["mac/mt_mac.c"]:
        raise SystemExit(f"Wrong TxS caller blob: {mac_blob}")
    mac = mac_original.decode("utf-8")
    mac_header_original = (root / "include/mac/mac.h").read_bytes()
    if git_blob(mac_header_original) != PINNED_BLOBS["include/mac/mac.h"]:
        raise SystemExit("Wrong MAC_TX_INFO source blob")
    mac_header = replace_once(
        mac_header_original.decode("utf-8"),
        "\tUINT32 TxSPriv;\n\tUCHAR PsmBySw;",
        "\tUINT32 TxSPriv;\n\tUINT32 TxSReservationGeneration;\n\tUINT8 TxSReservationPid;\n\tUCHAR PsmBySw;",
    )
    mac = replace_once(
        mac,
        "\tNdisZeroMemory(&txd, sizeof(TMAC_TXD_L));",
        "\tinfo->TxSReservationGeneration = 0;\n\tinfo->TxSReservationPid = 0;\n\tNdisZeroMemory(&txd, sizeof(TMAC_TXD_L));",
    )
    call = re.compile(
        r"(?P<indent>\t+)txd_5->pid = AddTxSStatus\((?P<args>.*?)\);\s*\n"
        r"(?P=indent)txd_5->tx_status_2_host = 1;", re.DOTALL
    )
    if len(call.findall(mac)) != 4:
        raise SystemExit("Expected four TxS caller sites")

    def checked_call(match: re.Match[str]) -> str:
        indent = match.group("indent")
        args = match.group("args").rstrip()
        reservation_output = (f"{indent}\tinfo->TxSReservationGeneration = status_generation;\n"
                              f"{indent}\tinfo->TxSReservationPid = status_pid;\n"
                              if "info->TxSPriv" in args else "")
        return (f"{indent}UINT8 status_pid;\n"
                f"{indent}UINT32 status_generation;\n"
                f"{indent}if (AddTxSStatus({args}, &status_pid, &status_generation) == 0) {{\n"
                f"{indent}\ttxd_5->pid = status_pid;\n"
                f"{reservation_output}"
                f"{indent}\ttxd_5->tx_status_2_host = 1;\n"
                f"{indent}}} else {{\n"
                f"{indent}\ttxd_5->tx_status_2_host = 0;\n"
                f"{indent}}}")

    mac = call.sub(checked_call, mac)
    payload = data.encode("utf-8")
    target = output / "tx_rx" / "txs.c"
    target.parent.mkdir(parents=True)
    target.write_bytes(payload)
    header_target = output / "include/mac/mac_mt/mt_mac.h"
    header_target.parent.mkdir(parents=True)
    header_payload = header.encode("utf-8")
    header_target.write_bytes(header_payload)
    mac_target = output / "mac/mt_mac.c"
    mac_target.parent.mkdir(parents=True)
    mac_payload = mac.encode("utf-8")
    mac_target.write_bytes(mac_payload)
    mac_header_target = output / "include/mac/mac.h"
    mac_header_target.write_bytes(mac_header.encode("utf-8"))
    manifest = {
        "source_git_blobs": PINNED_BLOBS,
        "candidate_sha256": {
            "tx_rx/txs.c": hashlib.sha256(payload).hexdigest(),
            "include/mac/mac_mt/mt_mac.h": hashlib.sha256(header_payload).hexdigest(),
            "mac/mt_mac.c": hashlib.sha256(mac_payload).hexdigest(),
            "include/mac/mac.h": hashlib.sha256(mac_header.encode("utf-8")).hexdigest(),
        },
        "production_installed": False,
        "target_compiled": False,
        "txs_status_lock_staged": True,
        "occupied_pid_overwrite_prevented": True,
        "generation_tagged_pre_submit_cancel_staged": True,
        "beacon_cancel_caller_bound": False,
        "mac_tx_info_generation_output_staged": True,
        "mac_tx_info_pid_output_staged": True,
        "pid_reuse_safety_proved": False,
        "callback_quiescence_proved": False,
        "iot_bss_retirement_proved": False,
        "beacon_txs_index_bounded": True,
        "beacon_txs_state_lock_staged": True,
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
