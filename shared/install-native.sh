#!/usr/bin/env bash
set -euo pipefail

version="${1:-0.23.1}"
version="${version#v}"
if [[ "$version" != "0.23.1" ]]; then
  echo "::error::asdecided-ci does not have a verified checksum for asdecided-core $version"
  exit 1
fi

case "${RUNNER_OS:-}-$(uname -m)" in
  Linux-x86_64)
    archive="asdecided-x86_64-unknown-linux-gnu.tar.gz"
    digest="51cce8025a7cb2f8b2caea93a8ea71be0ad8c5c316fd0ecced688267bf97b8ac"
    executable="decided"
    ;;
  macOS-arm64)
    archive="asdecided-aarch64-apple-darwin.tar.gz"
    digest="40d7129541609cbcf967f7d7d453e7689412bbaac81aa8d3c84e636367804628"
    executable="decided"
    ;;
  Windows-x86_64)
    archive="asdecided-x86_64-pc-windows-msvc.zip"
    digest="14e3fd9b1c693a11f364f51587f74ec7f9ba6fa09ae183e049bc4b378d35cd25"
    executable="decided.exe"
    ;;
  *)
    echo "::error::Unsupported runner: ${RUNNER_OS:-unknown} $(uname -m)"
    exit 1
    ;;
esac

install_dir="${RUNNER_TEMP}/asdecided-${version}"
download="${RUNNER_TEMP}/${archive}"
url="https://github.com/itsthelore/asdecided-core/releases/download/v${version}/${archive}"

mkdir -p "$install_dir"
curl --fail --location --retry 3 --silent --show-error "$url" --output "$download"

if command -v sha256sum >/dev/null 2>&1; then
  echo "$digest  $download" | sha256sum --check -
else
  actual="$(shasum -a 256 "$download" | awk '{print $1}')"
  [[ "$actual" == "$digest" ]] || {
    echo "::error::Checksum mismatch for $archive"
    exit 1
  }
fi

if [[ "$archive" == *.zip ]]; then
  unzip -q "$download" -d "$install_dir"
else
  tar -xzf "$download" -C "$install_dir"
fi

echo "$install_dir" >> "$GITHUB_PATH"
"$install_dir/$executable" --version
