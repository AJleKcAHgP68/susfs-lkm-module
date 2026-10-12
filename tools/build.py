#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Build a pinned, hash-verified multi-KMI arm64 KernelSU module ZIP."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TAG = "v2.3.0-r17-fix-51c2169"
COMMIT = "51c2169e728c8c5c0f47e733839f6d1f187d504e"
URL = f"https://github.com/inforcqb/susfs4ksu-lkm/releases/download/{TAG}/"
ASSETS = {
    "susfs_guard_lkm-android12-5.10.ko": "c5f68beb3159fd3613827a68bc26d1393ca7c146c347eea3a06575522f292aa8",
    "susfs_guard_lkm-android13-5.10.ko": "efd8c80003ece090d333a7a8e1741fa202a6d1f7412df3648e2ffb97abfc1606",
    "susfs_guard_lkm-android13-5.15.ko": "12b42820880a1a103c5946ca9ac82496e5888e545789693d5fecfd96df2a5b96",
    "susfs_guard_lkm-android14-5.15.ko": "3bce43a55a2b105c22274c2a5dce2ab207a9e18eff2ecd612e005659a48c0c04",
    "susfs_guard_lkm-android14-6.1.ko": "3c3d0f07466f79e069c3cb1bbf3c04da57ef31da345f6bfbb62f4ac60642d1e5",
    "susfs_guard_lkm-android15-6.6.ko": "cae2730a0a2b42b00a8e80a605d052c78d607370a3c1cd1462a066ea44c36052",
    "susfs_guard_lkm-android16-6.12.ko": "c108e630882c9d99b2a61f0419626477ae65ccf427d4e53ed327f4259b460edf",
    "susfs_insmod": "2c23e2259d5ad4d324add01caa6e0d9a03d0e34ee7f112237176568d12630608",
}


def download(url, path, digest=None):
    if not path.exists():
        request = urllib.request.Request(url, headers={"User-Agent": "susfs-lkm-module-builder"})
        with urllib.request.urlopen(request, timeout=60) as response:
            path.write_bytes(response.read())
    if digest and hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise RuntimeError(f"SHA-256 mismatch: {path.name}")


def main():
    build = ROOT / "build"
    build.mkdir(exist_ok=True)
    sdk = Path(os.environ.get("ANDROID_HOME", str(Path.home() / "Android/Sdk")))
    ndk_env = os.environ.get("ANDROID_NDK_HOME")
    ndk = Path(ndk_env) if ndk_env else sorted((sdk / "ndk").iterdir(), key=lambda p: tuple(int(n) for n in p.name.split('.')))[-1]
    clang = ndk / "toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android28-clang"
    probe = build / "susfs_probe"
    subprocess.run([str(clang), "-O2", "-Wall", "-Wextra", "-Werror", "-fPIE", "-pie",
                    str(ROOT / "tools/susfs_probe.c"), "-o", str(probe)], check=True)
    for name, digest in ASSETS.items():
        download(URL + name, build / name, digest)
    source = build / "upstream-source.tar.gz"
    download(f"https://api.github.com/repos/inforcqb/susfs4ksu-lkm/tarball/{COMMIT}", source,
             "402e6ac69c35912f057e481edc30090c7ba1bff240647beba19f1d72b73c5ce2")
    provenance = {"repository": "https://github.com/inforcqb/susfs4ksu-lkm", "tag": TAG,
                   "commit": COMMIT, "assets_sha256": ASSETS,
                   "architecture": "arm64", "wrapper_version": "0.2.0",
                   "supported_kmis": sorted(name.removeprefix("susfs_guard_lkm-").removesuffix(".ko")
                                            for name in ASSETS if name.endswith(".ko")),
                   "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    output = dist / "susfs-lkm-module-0.2.0-arm64-multi-kmi.zip"
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted((ROOT / "module").rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(ROOT / "module"))
        archive.write(probe, "bin/susfs_probe")
        archive.write(build / "susfs_insmod", "bin/susfs_insmod")
        for name in sorted(ASSETS):
            if name.endswith(".ko"):
                archive.write(build / name, "lib/" + name)
        archive.write(source, "source/upstream-source.tar.gz")
        archive.write(ROOT / "tools/susfs_probe.c", "source/susfs_probe.c")
        archive.write(ROOT / "LICENSE", "LICENSE")
        archive.writestr("provenance.json", json.dumps(provenance, indent=2) + "\n")
    print(output)
    print("sha256:", hashlib.sha256(output.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
