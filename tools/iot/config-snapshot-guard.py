"""Verify the exact existing native snapshot contract before enabling SET."""
from pathlib import Path
import hashlib

PREPARED_GETALL = "1328a1e4fa4f098286ce7a30561ebb51f645010e6fcb6c4b7182000bb721ef08"
PREPARED_GENERATE = "c25f6619194849e9c2897c6ea73aff9b935aaf88a52afb037a2a2069a5d3cef1"
NATIVE_HEADER = "411b381cdff5d6fea5fda76510e7a5dacff591dd067ce47c3cc3e225ae42b33e"


def verify(trunk: Path, rc: Path):
    kernel = trunk / "linux-4.4.x/drivers/nvram/nvram.c"
    config = trunk / ".config"
    kernel_config = trunk / "linux-4.4.x/.config"
    native_header = trunk / "linux-4.4.x/include/nvram/bcmnvram.h"
    library = Path(__file__).resolve().parent.parent / "band-steering"
    for path in (kernel, config, kernel_config, native_header, rc / "Makefile", rc / "wr-band-settings-snapshot.c",
                 rc / "wr-band-settings-snapshot.h"):
        if path.is_symlink() or not path.is_file():
            raise ValueError("Missing or linked native snapshot input: " + str(path))
    selections = config.read_text().splitlines()
    if selections.count("CONFIG_FIRMWARE_INCLUDE_WR_BAND_STEERING=y") != 1 or \
            "# CONFIG_FIRMWARE_INCLUDE_WR_BAND_STEERING is not set" in selections:
        raise ValueError("Native snapshot provider requires selected Band Steering")
    text = kernel.read_text()
    start = text.index("int\n_nvram_getall(")
    end = text.index("\n}", start) + 2
    digest = hashlib.sha256(text[start:end].encode()).hexdigest()
    if digest != PREPARED_GETALL or text.count("#include <linux/errno.h>\n") != 1:
        raise ValueError("Native getall overflow refusal is not the pinned prepared function")
    start = text.index("int\n_nvram_generate(")
    end = text.index("\n}", start) + 2
    generated = hashlib.sha256(text[start:end].encode()).hexdigest()
    if generated != PREPARED_GENERATE:
        raise ValueError("Native consolidation/flash overflow refusal is not prepared")
    if hashlib.sha256(native_header.read_bytes()).hexdigest() != NATIVE_HEADER:
        raise ValueError("Native NVRAM capacity/layout header differs from the pinned source")
    kernel_selections = kernel_config.read_text().splitlines()

    def enabled(name):
        assignments = [line for line in kernel_selections if line.startswith(name + "=")]
        if len(assignments) > 1 or any(line not in (name + "=y", name + "=m") for line in assignments):
            raise ValueError("Ambiguous native NVRAM configuration: " + name)
        if name + "=y" in assignments and "# " + name + " is not set" in kernel_selections:
            raise ValueError("Contradictory native NVRAM configuration: " + name)
        return name + "=y" in assignments

    # Exact branches of the hash-pinned header, not an inferred board capacity.
    nand = enabled("CONFIG_MTD_NAND_RALINK") or enabled("CONFIG_MTD_NAND_MTK")
    space = (0x1F000 if enabled("CONFIG_MTD_NAND_USE_UBI_PART") else 0x20000) if nand else 0xF000
    expected = (library / "settings-snapshot.c").read_bytes().replace(
        b'"settings-snapshot.h"', b'"wr-band-settings-snapshot.h"'
    )
    actual = (rc / "wr-band-settings-snapshot.c").read_bytes()
    header = (rc / "wr-band-settings-snapshot.h").read_bytes()
    if actual != expected or header != (library / "settings-snapshot.h").read_bytes():
        raise ValueError("Native owned snapshot implementation differs")
    if "wr-band-settings-snapshot.o" not in (rc / "Makefile").read_text():
        raise ValueError("Native snapshot object is not linked")
    return {"verified": True, "kernel_getall_sha256": digest,
            "kernel_generate_sha256": generated,
            "native_header_sha256": NATIVE_HEADER, "nvram_space": space,
            "nvram_header_bytes": 20,
            "snapshot_c_sha256": hashlib.sha256(actual).hexdigest(),
            "snapshot_h_sha256": hashlib.sha256(header).hexdigest()}


def marker(evidence):
    prepared = evidence.get("verified") is True
    values = {"WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED": int(prepared),
              "WR_IOT_NATIVE_NVRAM_SPACE": evidence["nvram_space"] if prepared else 0,
              "WR_IOT_NATIVE_NVRAM_HEADER_BYTES": evidence["nvram_header_bytes"] if prepared else 0}
    return "".join("#ifndef " + name + "\n#define " + name + " " + str(value) + "\n#endif\n"
                   for name, value in values.items())
