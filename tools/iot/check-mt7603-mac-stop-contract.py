#!/usr/bin/env python3
"""Check the pinned MT7603 MAC stop write/readback boundary.

This source-shape gate does not prove MMIO completion or DMA quiescence.
"""

import argparse
import re
from pathlib import Path


EXPECTED_WRITES = [
    "RTMP_IO_WRITE32(pAd, ARB_SCR, Value);",
    "RTMP_IO_WRITE32(pAd, ARB_TQCR0, Value1);",
    "RTMP_IO_WRITE32(pAd, ARB_RQCR, Value2);",
    "RTMP_IO_WRITE32(pAd, WF_PHY_BASE + 0x426c, Value3);",
]
EXPECTED_READS = [
    "RTMP_IO_READ32(pAd, ARB_SCR, &Value);",
    "RTMP_IO_READ32(pAd, ARB_TQCR0, &Value1);",
    "RTMP_IO_READ32(pAd, ARB_RQCR, &Value2);",
    "RTMP_IO_READ32(pAd, WF_PHY_BASE + 0x426c, &Value3);",
]


def extract_function(source: str) -> str:
    signature = "INT32 AsicSetMacTxRx(RTMP_ADAPTER *pAd, INT32 TxRx, BOOLEAN Enable)"
    if source.count(signature) != 1:
        raise ValueError("AsicSetMacTxRx signature missing or ambiguous")
    start = source.index(signature)
    brace = source.index("{", start)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start:index + 1]
    raise ValueError("AsicSetMacTxRx body is unterminated")


def audit(source: str, linux_header: str | None = None) -> dict:
    body = extract_function(source)
    writes = re.findall(r"RTMP_IO_WRITE32\s*\([^;]+;", body)
    reads = re.findall(r"RTMP_IO_READ32\s*\([^;]+;", body)
    if writes != EXPECTED_WRITES:
        raise ValueError("AsicSetMacTxRx MMIO write set/order changed; review required")
    if reads != EXPECTED_READS:
        raise ValueError("AsicSetMacTxRx initial MMIO read set/order changed; review required")
    if not re.search(r"RTMP_IO_WRITE32\(pAd, WF_PHY_BASE \+ 0x426c, Value3\);"
                     r"\s*\n\s*return TRUE;", body):
        raise ValueError("reviewed write-to-return shape changed")
    pci_accessor = None
    if linux_header is not None:
        accessor = re.search(
            r"#define\s+_RTMP_IO_WRITE32\s*\([^\n]+\).*?\n(?=#(?:ifdef|if|else|endif))",
            linux_header, re.S)
        body = accessor.group(0) if accessor else ""
        pci_accessor = bool(
            re.search(r"#ifdef\s+RTMP_MAC_PCI\s+\#if[^\n]*\n.*?"
                      r"#define\s+_RTMP_IO_WRITE32", linux_header, re.S)
            and "bPCIclkOff" in body and "writel(" in body
            and "readl(" not in body and "RTMP_IO_READ32" not in body)
        if not pci_accessor:
            raise ValueError("active PCI _RTMP_IO_WRITE32 accessor changed")
    return {
        "write_registers": ["ARB_SCR", "ARB_TQCR0", "ARB_RQCR", "WF_PHY_BASE+0x426c"],
        "initial_reads": ["ARB_SCR", "ARB_TQCR0", "ARB_RQCR", "WF_PHY_BASE+0x426c"],
        "post_write_readback": False,
        "mmio_completion_proven": False,
        "dma_quiescence_proven": False,
        "active_pci_accessor_uses_writel": pci_accessor,
        "active_pci_accessor_readback": False if pci_accessor else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="pinned mt76x3 source root")
    parser.add_argument("--linux-header", type=Path,
                        help="matching include/os/rt_linux.h from the prepared target")
    args = parser.parse_args()
    source = args.source / "hw_ctrl/cmm_asic_mt.c"
    result = audit(source.read_text(encoding="utf-8"),
                   args.linux_header.read_text(encoding="utf-8")
                   if args.linux_header else None)
    print("PASS pinned MAC-stop shape; four writes, no post-write receipt; "
          "MMIO completion and DMA quiescence remain unproven")
    print("writes=" + ",".join(result["write_registers"]))
    if result["active_pci_accessor_uses_writel"]:
        print("active PCI accessor: writel(), no accessor readback")


if __name__ == "__main__":
    main()
