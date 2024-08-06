#!/usr/bin/env sh

set -euo pipefail
IFS=$'\n\t'


# TODO: autodetect arch. rn this is the only arch, though.
export DOWNLOAD_ARCH=x64

tmp=$(mktemp -d --suffix '.install-zcripts')
filename=install-zcripts_${DOWNLOAD_ARCH}.run
export DOWNLOAD_URL="https://github.com/corydodt/zcripts/releases/latest/download/${filename}"

curl -sSL -o"$tmp/${filename}" ${DOWNLOAD_URL}
trap 'rm -rvf $tmp' EXIT

$tmp/"$filename"
