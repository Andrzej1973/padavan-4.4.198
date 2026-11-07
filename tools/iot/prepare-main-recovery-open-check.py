"""Inject the real isolated main-open function into its host recovery fixture."""

import argparse
from pathlib import Path


def extract_function(source: str, signature: str) -> str:
    start = source.index(signature)
    opening = source.index("{", start)
    depth = 0
    for index in range(opening, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise ValueError("main-open function has no closing brace")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source = (args.candidate / "os/linux/rt_main_dev.c").read_text()
    function = extract_function(source, "int MainVirtualIF_open(struct net_device *net_dev)")
    if function.count("wr_iot_main_verify_recovery_submit(") != 1:
        raise ValueError("unexpected recovery submission count in extracted main open")
    fixture = Path(__file__).with_name("check-main-recovery-reaper.c").read_text()
    marker = "/* ACTUAL_MAIN_OPEN */"
    if fixture.count(marker) != 1:
        raise ValueError("fixture marker missing or duplicated")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "#define WR_IOT_EXTRACT_MAIN_OPEN 1\n" + fixture.replace(marker, function)
    )


if __name__ == "__main__":
    main()
