#!/bin/sh
# Build bin/macos/seqtk (or bin/linux/seqtk) from an unmodified seqtk tree.
# Usage: tools/seqtk-build/build_seqtk_macos.sh [path/to/seqtk-1.5]
# The POSIX C runtime already provides the drand48 family, so no shim is needed.
set -e

SRC="${1:-../../../seqtk-1.5}"
HERE="$(cd "$(dirname "$0")" && pwd)"

if [ ! -f "$SRC/seqtk.c" ]; then
    echo "[ERROR] seqtk.c not found under $SRC" >&2
    echo "        pass the source directory as the first argument." >&2
    exit 2
fi

case "$(uname -s)" in
    Darwin*) PLATFORM=macos ;;
    Linux*)  PLATFORM=linux ;;
    *)       PLATFORM=unknown ;;
esac

OUT="$HERE/../../bin/$PLATFORM"
mkdir -p "$OUT"

# Homebrew keeps zlib out of the default search path on Apple Silicon.
if [ "$PLATFORM" = macos ] && [ -d /opt/homebrew/opt/zlib ]; then
    ZLIB_FLAGS="-I/opt/homebrew/opt/zlib/include -L/opt/homebrew/opt/zlib/lib"
fi

echo "[1/2] compiling seqtk for $PLATFORM..."
# shellcheck disable=SC2086
cc -O2 -Wall $ZLIB_FLAGS "$SRC/seqtk.c" -o "$OUT/seqtk" -lz

echo "[2/2] checking the result..."
"$OUT/seqtk" 2>&1 | grep -q "Version:" || {
    echo "[ERROR] the binary did not report a version." >&2
    exit 1
}
echo "OK: $OUT/seqtk"
