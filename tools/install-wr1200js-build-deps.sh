#!/usr/bin/env bash
# CI-only apt source selection; do not alter the machine's saved apt configuration.
set -euo pipefail
. /etc/os-release
case "$ID:$VERSION_ID:$VERSION_CODENAME" in
  ubuntu:22.04:jammy|ubuntu:24.04:noble) ;;
  *) echo 'Unsupported WR1200JS build host' >&2; exit 1;;
esac
sources=$(mktemp)
trap 'rm -f -- "$sources"' EXIT
chmod 644 "$sources"
apt_options=(-o "Dir::Etc::sourcelist=$sources" -o Dir::Etc::sourceparts=-
  -o Acquire::Retries=1 -o Acquire::http::Timeout=20 -o Acquire::https::Timeout=20)
for attempt in 1 2; do
  archive=https://archive.ubuntu.com/ubuntu
  security=https://security.ubuntu.com/ubuntu
  if [ "$attempt" -eq 2 ]; then
    # Registered Ubuntu archive mirror, including security pockets. APT still
    # verifies signed metadata and package hashes using Ubuntu archive keys.
    archive=https://mirrors.xtom.com/ubuntu
    security=$archive
  fi
  : > "$sources"
  for suite in "$VERSION_CODENAME" "$VERSION_CODENAME-updates" "$VERSION_CODENAME-backports"; do
    echo "deb $archive $suite main restricted universe multiverse" >> "$sources"
  done
  echo "deb $security $VERSION_CODENAME-security main restricted universe multiverse" >> "$sources"
  echo "WR1200JS dependencies: Ubuntu $VERSION_ID attempt $attempt; archive=$archive security=$security"
  if sudo timeout --kill-after=15s 180s apt-get "${apt_options[@]}" -o APT::Update::Error-Mode=any update &&
     sudo timeout --kill-after=15s 420s apt-get "${apt_options[@]}" install --no-install-recommends -y \
       autoconf automake autopoint cmake bison build-essential flex \
       gawk gettext git gperf libtool libtool-bin pkg-config fakeroot \
       kmod cpio texinfo help2man libncurses-dev zlib1g-dev \
       libsqlite3-dev gcc-multilib curl dos2unix unzip wget xxd \
       libltdl-dev libgcrypt20-dev libgmp-dev libmpfr-dev libarchive-tools libblkid-dev \
       python3-docutils ccache squashfs-tools qemu-user-static dnsutils iptables proot; then
    exit 0
  fi
  echo "Dependency attempt $attempt failed" >&2
done
echo 'Build dependency installation failed after two bounded attempts' >&2
exit 1
