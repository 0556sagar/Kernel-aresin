# POCO F3 GT (`aresin`) Non-GKI KernelSU-Next `boot.img` Builder

A GitHub Actions repository template tailored for **POCO F3 GT (`aresin` / MT6893, non-GKI Linux 4.14)** that:
1. Compiles a non-GKI kernel with [**KernelSU-Next**](https://github.com/KernelSU-Next/KernelSU-Next) (`legacy` branch + automated 5-point manual hooks for Linux 4.14).
2. Unpacks your ROM's stock `boot.img` using `magiskboot` (`v30.7`, avoiding the `v31.0` AVB signed aux-block regression on Xiaomi MediaTek devices), injects the freshly built kernel, and repacks a ready-to-flash `boot-ksun-aresin-*.img`.
3. Automatically bundles the **latest KernelSU-Next Manager APK** from [KernelSU-Next Releases](https://github.com/KernelSU-Next/KernelSU-Next/releases) alongside your patched `boot.img`.

## Why Manual Hooks + `boot.img` Repack?

- **Manual hooks by default**: On POCO F3 GT / Redmi K40 Gaming (`ares` / `aresin`, kernel `4.14.186`), kprobes-based KernelSU hooks are known to cause bootloops ([KernelSU-Next Issue #19](https://github.com/KernelSU-Next/KernelSU-Next/issues/19)). `scripts/apply_ksun_manual_hooks.py` automatically patches `fs/exec.c`, `fs/open.c`, `fs/read_write.c`, `fs/stat.c`, and `kernel/reboot.c` per the [official KernelSU-Next non-GKI guide](https://kernelsu-next.github.io/webpage/pages/how-to-integrate-for-non-gki.html).
- **`boot.img` root method**: Repacking your exact stock `boot.img` preserves your ROM's original ramdisk, `init`, and DTB, allowing direct flashing via `fastboot flash boot` without requiring a custom recovery.

## Quick Start

1. **Push this repository to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial POCO F3 GT aresin KSU-Next boot.img builder"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo>.git
   git push -u origin main
   ```
2. **Provide your stock `boot.img`** (from the exact ROM currently installed on your POCO F3 GT):
   - Either pass a direct download URL in the **`stock_boot_url`** workflow input (or `STOCK_BOOT_URL` in `config/aresin.env`), **or**
   - Commit it to `stock_boot/boot.img` (`git add -f stock_boot/boot.img`).
3. **Check `config/aresin.env`**:
   - Defaults to [`Tkpointz/android_kernel_aresin`](https://github.com/Tkpointz/android_kernel_aresin) (`ares_user_defconfig`, ZyC Clang 14 + GCC 4.9 compat, `LLVM_IAS=false`).
   - Swap `KERNEL_REPO` / `KERNEL_BRANCH` if your ROM uses a different MT6893 4.14 kernel tree (such as [`AbzRaider/kernel_xiaomi_ares`](https://github.com/AbzRaider/kernel_xiaomi_ares)).
4. **Run the workflow**: Go to **Actions -> Build POCO F3 GT (aresin) KSU-Next boot.img -> Run workflow**.
5. **Flash & install**:
   - Download `boot-ksun-aresin-*.img` and the bundled latest `KernelSU-Next` Manager APK from the workflow artifacts (or GitHub Release).
   - Flash via fastboot (back up your stock `boot.img` first!):
     ```bash
     fastboot flash boot boot-ksun-aresin-*.img
     fastboot reboot
     ```
   - Install the bundled latest KernelSU-Next Manager APK and verify status shows **Working**.

## Optional Extras

- **Custom patches**: Drop `.patch` files into `patches/` to apply them automatically before KernelSU-Next hooks.
- **Telegram uploads**: Add `TG_BOT_TOKEN` and `TG_CHAT_ID` under **Settings -> Secrets and variables -> Actions**.
