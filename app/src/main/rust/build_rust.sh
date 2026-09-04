#!/bin/bash
set -e

if [ -f "$HOME/.cargo/env" ]; then
    . "$HOME/.cargo/env"
fi
export PATH="$HOME/.cargo/bin:$PATH"

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Resolve NDK LLVM toolchain path dynamically
if [ -n "$ANDROID_NDK_HOME" ] && [ -d "$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/bin" ]; then
    NDK_LLVM="$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/bin"
elif [ -n "$ANDROID_NDK_ROOT" ] && [ -d "$ANDROID_NDK_ROOT/toolchains/llvm/prebuilt/linux-x86_64/bin" ]; then
    NDK_LLVM="$ANDROID_NDK_ROOT/toolchains/llvm/prebuilt/linux-x86_64/bin"
elif [ -n "$ANDROID_HOME" ] && [ -d "$ANDROID_HOME/ndk/26.1.10909125/toolchains/llvm/prebuilt/linux-x86_64/bin" ]; then
    NDK_LLVM="$ANDROID_HOME/ndk/26.1.10909125/toolchains/llvm/prebuilt/linux-x86_64/bin"
elif [ -d "/opt/android/sdk/ndk/26.1.10909125/toolchains/llvm/prebuilt/linux-x86_64/bin" ]; then
    NDK_LLVM="/opt/android/sdk/ndk/26.1.10909125/toolchains/llvm/prebuilt/linux-x86_64/bin"
else
    # Fallback to any installed NDK version
    NDK_FOUND=$(find "${ANDROID_HOME:-/opt/android/sdk}/ndk" -maxdepth 1 -mindepth 1 2>/dev/null | head -n 1)
    if [ -n "$NDK_FOUND" ] && [ -d "$NDK_FOUND/toolchains/llvm/prebuilt/linux-x86_64/bin" ]; then
        NDK_LLVM="$NDK_FOUND/toolchains/llvm/prebuilt/linux-x86_64/bin"
    else
        echo "ERROR: Could not locate Android NDK Clang toolchain!"
        exit 1
    fi
fi

echo "Using NDK toolchain at: $NDK_LLVM"
export PATH="$NDK_LLVM:$PATH"

export CC_aarch64_linux_android="$NDK_LLVM/aarch64-linux-android24-clang"
export CARGO_TARGET_AARCH64_LINUX_ANDROID_LINKER="$NDK_LLVM/aarch64-linux-android24-clang"

export CC_x86_64_linux_android="$NDK_LLVM/x86_64-linux-android24-clang"
export CARGO_TARGET_X86_64_LINUX_ANDROID_LINKER="$NDK_LLVM/x86_64-linux-android24-clang"

cd "$DIR"
cargo build --release --target aarch64-linux-android
cargo build --release --target x86_64-linux-android

mkdir -p "$DIR/target/libs/arm64-v8a"
mkdir -p "$DIR/target/libs/x86_64"

cp "$DIR/target/aarch64-linux-android/release/libstrategy_core.a" "$DIR/target/libs/arm64-v8a/"
cp "$DIR/target/x86_64-linux-android/release/libstrategy_core.a" "$DIR/target/libs/x86_64/"
echo "Rust strategy_core static libraries built successfully for Android arm64-v8a and x86_64!"
