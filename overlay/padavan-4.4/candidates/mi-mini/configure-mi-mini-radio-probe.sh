#!/bin/sh
# Compile-probe configuration only. Not a MI-MINI boot/firmware configuration.
set -eu
kernel=$1
cross=$2
make -C "$kernel" ARCH=mips CROSS_COMPILE="$cross" rt305x_defconfig
cd "$kernel"
bash scripts/config --disable SOC_RT305X --disable SOC_RT288X \
    --disable SOC_RT3883 --disable SOC_MT7621 --enable SOC_MT7620 \
    --enable OF --enable NET --enable WIRELESS --enable WLAN \
    --enable WL_MEDIATEK --enable WIFI_DRIVER --enable MI_MINI_RADIO \
    --enable MTD --enable MTD_PARTITIONS \
    --enable RT2860V2_AP_LLTD --enable RT2860V2_AP_WDS \
    --enable RT2860V2_AP_MBSS --enable RT2860V2_AP_MBSS_NEW_MBSSID_MODE \
    --enable RT2860V2_AP_APCLI --enable RT2860V2_AP_GREENAP \
    --disable RT_ATE --disable RT_VIDEO_TURBINE --disable RA_HW_NAT_WIFI
make ARCH=mips CROSS_COMPILE="$cross" olddefconfig
for key in SOC_MT7620 MI_MINI_RADIO RT2860V2_AP RT2860V2_AP_WDS \
           RT2860V2_AP_MBSS RT2860V2_AP_APCLI; do
    grep -qx "CONFIG_${key}=y" .config || {
        echo "Required compile-probe selection did not survive Kconfig: $key" >&2
        exit 1
    }
done
if grep -qx 'CONFIG_SOC_MT7621=y' .config; then
    echo 'Probe configuration retained the wrong SoC' >&2
    exit 1
fi
make ARCH=mips CROSS_COMPILE="$cross" prepare
make ARCH=mips CROSS_COMPILE="$cross" -j2 \
    drivers/net/wireless/mediatek/mi-mini/ \
    drivers/net/wireless/wifi_utility/mt_wifi_mtd.o
echo 'Radio and MTD objects compiled; full vmlinux link and device runtime not verified.'
