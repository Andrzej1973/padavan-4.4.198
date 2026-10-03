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
    --set-val MI_MINI_RADIO_RAM_MB 128 --disable RT_MEMORY_OPTIMIZATION \
    --disable CC_OPTIMIZE_FOR_SIZE \
    --enable MTD --enable MTD_PARTITIONS --enable PCI --enable GPIO_SYSFS \
    --enable RT2860V2_AP_LLTD --enable RT2860V2_AP_WDS \
    --enable RT2860V2_AP_MBSS --enable RT2860V2_AP_MBSS_NEW_MBSSID_MODE \
    --enable RT2860V2_AP_APCLI --enable RT2860V2_AP_GREENAP \
    --disable RT_ATE --disable RT_VIDEO_TURBINE --disable RA_HW_NAT_WIFI
make ARCH=mips CROSS_COMPILE="$cross" olddefconfig
for key in SOC_MT7620 PCI GPIO_SYSFS MI_MINI_RADIO RT2860V2_AP RT2860V2_AP_WDS \
           RT2860V2_AP_MBSS RT2860V2_AP_APCLI; do
    grep -qx "CONFIG_${key}=y" .config || {
        echo "Required compile-probe selection did not survive Kconfig: $key" >&2
        exit 1
    }
done
grep -qx 'CONFIG_MI_MINI_RADIO_RAM_MB=128' .config || {
    echo 'Radio ring-sizing RAM setting did not survive Kconfig' >&2
    exit 1
}
if grep -qx 'CONFIG_SOC_MT7621=y' .config; then
    echo 'Probe configuration retained the wrong SoC' >&2
    exit 1
fi
make ARCH=mips CROSS_COMPILE="$cross" prepare
make ARCH=mips CROSS_COMPILE="$cross" -j2 \
    drivers/net/wireless/mediatek/mi-mini/ \
    drivers/net/wireless/wifi_utility/mt_wifi_mtd.o
echo 'Radio and MTD objects compiled; starting isolated full vmlinux link.'
make ARCH=mips CROSS_COMPILE="$cross" -j2 vmlinux
"${cross}nm" vmlinux > mi-mini-vmlinux-symbols.txt
for symbol in mi_mini_factory_read mi_mini_radio_attach mi_mini_probe; do
    grep -Eq " [tT] ${symbol}$" mi-mini-vmlinux-symbols.txt || {
        echo "Candidate symbol missing from linked kernel: $symbol" >&2
        exit 1
    }
done
echo 'Isolated vmlinux linked with the candidate; no board boot or firmware-image validation.'
