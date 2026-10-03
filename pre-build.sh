#!/bin/sh
set -eu

SCRIPT_PATH="${BASH_SOURCE[0]:-$0}"
ROOTDIR="$(CDPATH= cd -- "$(dirname -- "$SCRIPT_PATH")" && pwd)"
PADAVAN_DIR="$ROOTDIR/padavan-ng"
OVERLAY_DIR="$ROOTDIR/overlay/padavan-ng"
USER_MAKEFILE="$PADAVAN_DIR/trunk/user/Makefile"

if [ ! -f "$USER_MAKEFILE" ]; then
    echo "ERROR: nilabsent user Makefile not found: $USER_MAKEFILE" >&2
    exit 1
fi

# Hadzhioglu keeps the vlmcsd source tree alongside its package. The
# builder repository is intentionally kept small, so fetch the same source
# revision at build time before applying the overlay.
VLMCSD_DIR="$OVERLAY_DIR/trunk/user/vlmcsd"
VLMCSD_NAME="vlmcsd-svn1113"
VLMCSD_URL="https://github.com/Wind4/vlmcsd/archive/svn1113.tar.gz"
if [ ! -d "$VLMCSD_DIR/$VLMCSD_NAME" ]; then
    mkdir -p "$VLMCSD_DIR"
    wget -t5 --timeout=20 --no-check-certificate -O "$VLMCSD_DIR/$VLMCSD_NAME.tar.gz" "$VLMCSD_URL"
    tar -C "$VLMCSD_DIR" -xf "$VLMCSD_DIR/$VLMCSD_NAME.tar.gz"
    rm -f "$VLMCSD_DIR/$VLMCSD_NAME.tar.gz"
fi

# Import only the Hadzhioglu userspace USB/IP implementation. The nilabsent
# tree already supplies the kernel USB/IP support, so we deliberately do not
# replace any kernel sources. A sparse clone keeps the experimental builder
# small while preserving the upstream package layout exactly.
HADZHI_TMP="$ROOTDIR/.hadzhioglu-usbip"
HADZHI_COMMIT="503a6f0064bc5999bf92e47a902a732693a1a4f5"
rm -rf "$HADZHI_TMP"
if ! command -v git >/dev/null 2>&1; then
    echo "ERROR: git is required to import Hadzhioglu usbip/sysfsutils" >&2
    exit 1
fi
git clone --depth 1 --filter=blob:none --sparse https://gitlab.com/hadzhioglu/padavan-ng.git "$HADZHI_TMP"
HADZHI_ACTUAL_COMMIT="$(git -C "$HADZHI_TMP" rev-parse HEAD)"
if [ "$HADZHI_ACTUAL_COMMIT" != "$HADZHI_COMMIT" ]; then
    echo "ERROR: expected Hadzhioglu $HADZHI_COMMIT, got $HADZHI_ACTUAL_COMMIT" >&2
    exit 1
fi
git -C "$HADZHI_TMP" sparse-checkout set trunk/user/usbip trunk/user/sysfsutils
mkdir -p "$PADAVAN_DIR/trunk/user"
rm -rf "$PADAVAN_DIR/trunk/user/usbip" "$PADAVAN_DIR/trunk/user/sysfsutils"
cp -a "$HADZHI_TMP/trunk/user/usbip" "$PADAVAN_DIR/trunk/user/"
cp -a "$HADZHI_TMP/trunk/user/sysfsutils" "$PADAVAN_DIR/trunk/user/"
rm -rf "$HADZHI_TMP"

# Apply only the experimental package overlay. clear_tree.sh does not
# remove these source files, so the overlay remains available to the build.
if [ -d "$OVERLAY_DIR" ]; then
    cp -a "$OVERLAY_DIR"/. "$PADAVAN_DIR"/
fi

# Apply every experimental source patch in lexical order. Keeping each
# logical change in a separate patch makes the branch easy to review/revert.
for PATCH_FILE in "$ROOTDIR"/overlay/patches/*.patch; do
    [ -f "$PATCH_FILE" ] || continue
    # Normalize the two harmless formatting variants present in older patches.
    sed -i -e 's/^ diff --git/diff --git/' -e 's/^ @@/@@/' "$PATCH_FILE"
    patch -d "$PADAVAN_DIR" -p1 --forward < "$PATCH_FILE"
done

append_make_dir() {
    line="$1"
    if ! grep -Fqx "$line" "$USER_MAKEFILE"; then
        printf '\n%s\n' "$line" >> "$USER_MAKEFILE"
    fi
}

# These options already exist in the WR1200JS build.config.
# The current nilabsent tree has no corresponding user-package build hooks.
append_make_dir 'dir_$(CONFIG_FIRMWARE_INCLUDE_VLMCSD) += vlmcsd'
append_make_dir 'dir_$(CONFIG_FIRMWARE_INCLUDE_NDISC6_RDISC6) += ndisc6'
append_make_dir 'dir_$(CONFIG_FIRMWARE_INCLUDE_SOCAT) += socat'

echo "Experimental Hadzhioglu package overlay applied:"
echo "  - vlmcsd / KMS"
echo "  - ndisc6 + rdisc6"
echo "  - socat"
echo "  - USB/IP userspace + sysfsutils"
echo "  - Stubby options / WebUI"
