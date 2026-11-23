#!/usr/bin/env python3
"""
Applies KernelSU-Next 5-point manual hooks for non-GKI Linux 4.14 (MT6893 / aresin).
Targets:
  1. fs/exec.c       -> ksu_handle_execveat / ksu_handle_execveat_sucompat
  2. fs/open.c       -> ksu_handle_faccessat
  3. fs/read_write.c -> ksu_handle_vfs_read
  4. fs/stat.c       -> ksu_handle_stat
  5. kernel/reboot.c -> ksu_handle_sys_reboot
"""

import re
from pathlib import Path


def patch_file(path_str: str, marker: str, transform_fn) -> None:
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"Missing kernel file: {path_str}")
    src = path.read_text(encoding="utf-8", errors="ignore")
    if marker in src:
        print(f"[SKIP] {path_str} already patched.")
        return
    updated = transform_fn(src)
    if updated == src:
        raise RuntimeError(f"Failed to match hook anchor in {path_str}")
    path.write_text(updated, encoding="utf-8")
    print(f"[OK] Patched {path_str}")


def patch_exec(src: str) -> str:
    decl = (
        "#ifdef CONFIG_KSU\n"
        "extern bool ksu_execveat_hook __read_mostly;\n"
        "extern int ksu_handle_execveat(int *fd, struct filename **filename_ptr, void *argv,\n"
        "                               void *envp, int *flags);\n"
        "extern int ksu_handle_execveat_sucompat(int *fd, struct filename **filename_ptr,\n"
        "                                        void *argv, void *envp, int *flags);\n"
        "#endif\n"
    )
    hook = (
        "#ifdef CONFIG_KSU\n"
        "\tif (unlikely(ksu_execveat_hook))\n"
        "\t\tksu_handle_execveat(&fd, &filename, &argv, &envp, &flags);\n"
        "\telse\n"
        "\t\tksu_handle_execveat_sucompat(&fd, &filename, &argv, &envp, &flags);\n"
        "#endif\n"
    )
    pattern = r"(static int do_execveat_common\s*\([^)]*\)\s*\{)"
    m = re.search(pattern, src)
    if not m:
        return src
    src = src[: m.start()] + decl + src[m.start() :]
    m2 = re.search(r"(return do_execve_common\(filename, argv, envp\);|if \(IS_ERR\(filename\)\))", src)
    if not m2:
        return src
    return src[: m2.start()] + hook + "\t" + src[m2.start() :]


def patch_open(src: str) -> str:
    decl = (
        "#ifdef CONFIG_KSU\n"
        "extern int ksu_handle_faccessat(int *dfd, const char __user **filename_user, int *mode,\n"
        "                                int *flags);\n"
        "#endif\n"
    )
    hook = (
        "#ifdef CONFIG_KSU\n"
        "\tksu_handle_faccessat(&dfd, &filename, &mode, NULL);\n"
        "#endif\n"
    )
    pattern = r"(SYSCALL_DEFINE3\s*\(\s*faccessat\s*,[^)]*\)\s*\{)"
    m = re.search(pattern, src)
    if not m:
        return src
    return src[: m.start()] + decl + src[m.start() : m.end()] + "\n" + hook + src[m.end() :]


def patch_read_write(src: str) -> str:
    decl = (
        "#ifdef CONFIG_KSU\n"
        "extern bool ksu_vfs_read_hook __read_mostly;\n"
        "extern int ksu_handle_vfs_read(struct file **file_ptr, char __user **buf_ptr,\n"
        "                               size_t *count_ptr, loff_t **pos);\n"
        "#endif\n"
    )
    hook = (
        "#ifdef CONFIG_KSU\n"
        "\tif (unlikely(ksu_vfs_read_hook))\n"
        "\t\tksu_handle_vfs_read(&file, &buf, &count, &pos);\n"
        "#endif\n"
    )
    pattern = r"(ssize_t vfs_read\s*\([^)]*\)\s*\{)"
    m = re.search(pattern, src)
    if not m:
        return src
    return src[: m.start()] + decl + src[m.start() : m.end()] + "\n" + hook + src[m.end() :]


def patch_stat(src: str) -> str:
    decl = (
        "#ifdef CONFIG_KSU\n"
        "extern int ksu_handle_stat(int *dfd, const char __user **filename_user, int *flags);\n"
        "#endif\n"
    )
    hook = (
        "#ifdef CONFIG_KSU\n"
        "\tksu_handle_stat(&dfd, &filename, &flags);\n"
        "#endif\n"
    )
    pattern = r"(int vfs_statx\s*\([^)]*\)\s*\{)"
    m = re.search(pattern, src)
    if not m:
        return src
    return src[: m.start()] + decl + src[m.start() : m.end()] + "\n" + hook + src[m.end() :]


def patch_reboot(src: str) -> str:
    decl = (
        "#ifdef CONFIG_KSU\n"
        "extern int ksu_handle_sys_reboot(int magic1, int magic2, unsigned int cmd, void __user **arg);\n"
        "#endif\n"
    )
    hook = (
        "#ifdef CONFIG_KSU\n"
        "\tksu_handle_sys_reboot(magic1, magic2, cmd, &arg);\n"
        "#endif\n"
    )
    pattern = r"(SYSCALL_DEFINE4\s*\(\s*reboot\s*,[^)]*\)\s*\{)"
    m = re.search(pattern, src)
    if not m:
        return src
    return src[: m.start()] + decl + src[m.start() : m.end()] + "\n" + hook + src[m.end() :]


def main() -> None:
    patch_file("fs/exec.c", "ksu_handle_execveat", patch_exec)
    patch_file("fs/open.c", "ksu_handle_faccessat", patch_open)
    patch_file("fs/read_write.c", "ksu_handle_vfs_read", patch_read_write)
    patch_file("fs/stat.c", "ksu_handle_stat", patch_stat)
    patch_file("kernel/reboot.c", "ksu_handle_sys_reboot", patch_reboot)


if __name__ == "__main__":
    main()
