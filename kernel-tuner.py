#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
  Kernel Tuner v2.1  |  Python Edition  |  Finglish UI
============================================================
  Support:
    - Debian 11/12/13 + sid
    - Ubuntu 20.04 / 22.04 / 24.04 / 24.10 / 25.04 +
  Features:
    - XanMod (MAIN / LTS / EDGE / RT)
    - Liquorix
    - Debian Official / Ubuntu Official / Ubuntu Mainline
    - 5 Profile + 1 Custom
    - Auto backup / restore
    - CPU level detection (x86-64-v1..v4)
============================================================
"""

import os
import re
import sys
import subprocess
import shutil
import time
import platform
from pathlib import Path
from datetime import datetime

# ============================================================
#  ANSI COLORS
# ============================================================
class C:
    R  = "\033[0;31m"
    G  = "\033[0;32m"
    Y  = "\033[1;33m"
    B  = "\033[0;34m"
    M  = "\033[0;35m"
    CY = "\033[0;36m"
    W  = "\033[1;37m"
    N  = "\033[0m"
    BD = "\033[1m"
    DM = "\033[2m"


def hr():
    print(f"{C.DM}{'─' * 62}{C.N}")


def hr2():
    print(f"{C.CY}{'═' * 62}{C.N}")


def log(msg):
    print(f"{C.G}  ✔{C.N} {msg}")


def warn(msg):
    print(f"{C.Y}  ⚠{C.N} {msg}")


def err(msg):
    print(f"{C.R}  ✘{C.N} {msg}")


def info(msg):
    print(f"{C.B}  ℹ{C.N} {msg}")


def step(msg):
    print(f"\n{C.CY}{C.BD}▶ {msg}{C.N}")


def pause():
    input(f"\n{C.DM}  Press Enter to continue...{C.N}")


# ============================================================
#  CONSTANTS
# ============================================================
SYSCTL_DIR   = Path("/etc/sysctl.d")
PROFILE_FILE = SYSCTL_DIR / "99-kernel-profile.conf"
BACKUP_DIR   = SYSCTL_DIR / f"backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
LOG_FILE     = Path("/var/log/kernel-tuner.log")
KEYRING_PATH = Path("/etc/apt/keyrings/xanmod-archive-keyring.gpg")
XANMOD_REPO  = Path("/etc/apt/sources.list.d/xanmod-release.list")

# XanMod codename haye rasmi (az site xanmod.org)
XANMOD_SUPPORTED = {
    "bookworm", "trixie", "forky", "sid",
    "noble", "plucky", "questing", "resolute", "stonking",
    "faye", "gigi", "wilma", "xia", "zara", "zena",
}

# Fallback baraye codename haye ghadimi
XANMOD_FALLBACK = {
    "focal":    "bookworm",
    "jammy":    "bookworm",
    "kinetic":  "bookworm",
    "lunar":    "bookworm",
    "mantic":   "bookworm",
    "oracular": "noble",
}


# ============================================================
#  HELPERS
# ============================================================
def run(cmd, check=False, capture=False, timeout=None):
    try:
        if capture:
            r = subprocess.run(
                cmd,
                shell=isinstance(cmd, str),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return r.returncode, r.stdout.strip(), r.stderr.strip()
        else:
            r = subprocess.run(
                cmd,
                shell=isinstance(cmd, str),
                timeout=timeout,
            )
            if check and r.returncode != 0:
                raise subprocess.CalledProcessError(r.returncode, cmd)
            return r.returncode, "", ""
    except FileNotFoundError as e:
        return 127, "", str(e)
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except Exception as e:
        return 1, "", str(e)


def apt_update():
    run("apt-get update -y", capture=True)


def apt_install(*pkgs):
    cmd = ["apt-get", "install", "-y"] + list(pkgs)
    r = subprocess.run(cmd)
    return r.returncode == 0


def write_log(msg):
    try:
        with open(LOG_FILE, "a") as f:
            f.write(f"[{datetime.now().isoformat()}] {msg}\n")
    except Exception:
        pass


# ============================================================
#  PRE-CHECKS
# ============================================================
def check_root():
    if os.geteuid() != 0:
        print(f"{C.R}{C.BD}")
        print("  ┌────────────────────────────────────────────────┐")
        print("  │  Must be run as root!                      │")
        print("  │  Use:  sudo python3 kernel-tuner.py   │")
        print("  └────────────────────────────────────────────────┘")
        print(f"{C.N}")
        sys.exit(1)


def detect_distro():
    release = Path("/etc/os-release")
    if not release.exists():
        err("OS release file not found.")
        sys.exit(1)

    data = {}
    for line in release.read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip().strip('"')

    distro_id = data.get("ID", "unknown").lower()
    codename  = data.get("VERSION_CODENAME", "").lower()
    version   = data.get("VERSION_ID", "?")
    pretty    = data.get("PRETTY_NAME", distro_id)

    if not codename:
        err("Codename not detected. Required for XanMod..")
        sys.exit(1)

    return distro_id, codename, version, pretty


def check_arch():
    arch = platform.machine().lower()
    if arch in ("x86_64", "amd64"):
        return "amd64"
    if arch in ("aarch64", "arm64"):
        err("ARM64 is not officially supported by XanMod yet..")
        sys.exit(1)
    err(f"Architecture {arch} support nemishe.")
    sys.exit(1)


def check_network():
    rc, _, _ = run("ping -c1 -W3 1.1.1.1", capture=True)
    if rc != 0:
        warn("Network ping failed, continuing (ICMP may be blocked).")


# ============================================================
#  CPU LEVEL DETECTION
# ============================================================
def detect_cpu_level():
    try:
        cpuinfo = Path("/proc/cpuinfo").read_text().lower()
    except Exception:
        return 2

    def has(flag):
        return f" {flag} " in cpuinfo or f" {flag}\n" in cpuinfo

    # v4
    if all(has(f) for f in ("avx512f", "avx512bw", "avx512cd", "avx512dq", "avx512vl")):
        return 4
    # v3
    if all(has(f) for f in ("avx2", "bmi2", "fma", "movbe", "f16c")):
        return 3
    # v2
    if all(has(f) for f in ("sse4_2", "popcnt", "cx16", "lahf_lm")):
        return 2
    return 1


# ============================================================
#  XANMOD
# ============================================================
def resolve_xanmod_codename(distro_id, codename):
    if codename in XANMOD_SUPPORTED:
        return codename, False
    fallback = XANMOD_FALLBACK.get(codename, "bookworm")
    return fallback, True


def setup_xanmod_repo(codename):
    KEYRING_PATH.parent.mkdir(parents=True, exist_ok=True)

    # GPG key
    if not KEYRING_PATH.exists():
        step("Downloading XanMod GPG key...")
        rc, _, errmsg = run(
            f"wget -qO - https://dl.xanmod.org/archive.key | "
            f"gpg --dearmor -vo {KEYRING_PATH}",
            capture=True,
        )
        if rc != 0 or not KEYRING_PATH.exists():
            err(f"GPG key install failed: {errmsg}")
            return False
    else:
        info(f"GPG key already exists: {KEYRING_PATH}")

    # Repo file — mesle site: http
    repo_line = (
        f"deb [signed-by={KEYRING_PATH}] "
        f"http://deb.xanmod.org {codename} main"
    )
    XANMOD_REPO.write_text(repo_line + "\n")
    log(f"Repo written: {repo_line}")

    # Update
    step("apt update...")
    rc, out, errmsg = run("apt-get update -y", capture=True)
    if rc != 0:
        warn("apt update finished with warnings.")
        write_log(f"apt update err: {errmsg[-500:]}")
    return True


def install_xanmod(branch="lts"):
    step(f"XanMod nasb mishe (branch: {branch.upper()})...")

    distro_id, codename, version, pretty = detect_distro()

    final_codename, used_fallback = resolve_xanmod_codename(distro_id, codename)
    if used_fallback:
        warn(f"Codename '{codename}' dar XanMod not found.")
        info(f"Fallback: '{final_codename}' will be used.")
    else:
        info(f"Codename '{codename}' directly supported.")

    apt_update()
    if not apt_install("wget", "gnupg", "ca-certificates", "curl"):
        err("Dependencies not installed.")
        return False

    if not setup_xanmod_repo(final_codename):
        return False

    cpu_level = detect_cpu_level()
    info(f"CPU psABI level: x86-64-v{cpu_level}")

    if cpu_level == 1 and branch != "lts":
        warn(f"Branch {branch} baraye v1 does not exist. Be LTS switch.")
        branch = "lts"
    if cpu_level == 4:
        warn("v4 (AVX-512) baraye kernel soodi nadare. v3 will be used.")
        cpu_level = 3

    pkg_map = {
        "main": {
            2: "linux-xanmod-x64v2",
            3: "linux-xanmod-x64v3",
        },
        "edge": {
            2: "linux-xanmod-edge-x64v2",
            3: "linux-xanmod-edge-x64v3",
        },
        "lts": {
            1: "linux-xanmod-lts-x64v1",
            2: "linux-xanmod-lts-x64v2",
            3: "linux-xanmod-lts-x64v3",
        },
        "rt": {
            2: "linux-xanmod-rt-x64v2",
            3: "linux-xanmod-rt-x64v3",
        },
    }

    pkg = pkg_map.get(branch, {}).get(cpu_level)
    if not pkg:
        err(f"Package baraye branch={branch}, level=v{cpu_level} not found.")
        return False

    info(f"Package: {pkg}")

    if not apt_install(pkg):
        warn(f"Nasb {pkg} failed khord. Fallback...")
        for alt in (
            "linux-xanmod-lts-x64v2",
            "linux-xanmod-lts-x64v3",
            "linux-xanmod-x64v3",
            "linux-xanmod",
        ):
            info(f"Emtehan: {alt}")
            if apt_install(alt):
                pkg = alt
                break
        else:
            err("No XanMod package installed.")
            return False

    log(f"XanMod installed: {pkg}")
    return True


def clean_xanmod():
    step("Cleaning XanMod repo and keyring")
    for p in (XANMOD_REPO, KEYRING_PATH):
        if p.exists():
            p.unlink()
            log(f"Removed: {p}")
    apt_update()
    log("XanMod repo cleaned.")


# ============================================================
#  LIQUORIX
# ============================================================
def install_liquorix():
    step("Liquorix installing...")
    apt_update()
    if not apt_install("wget", "gnupg", "ca-certificates", "curl"):
        err("Dependency install failed.")
        return False

    rc, out, errmsg = run(
        "curl -fsSL https://liquorix.net/install-liquorix.sh | bash",
        capture=True,
    )
    if rc != 0:
        err(f"Liquorix script error: {errmsg[:200]}")
        return False

    rc, out, _ = run("dpkg -l | grep -c '^ii  linux-image.*liquorix'", capture=True)
    if rc == 0 and out and int(out) > 0:
        log("Liquorix installed.")
        return True

    err("Liquorix install failed.")
    return False


# ============================================================
#  OFFICIAL KERNELS
# ============================================================
def install_debian_official():
    step("Debian Official Kernel")
    apt_update()
    ok = apt_install("linux-image-amd64", "linux-headers-amd64", "firmware-linux")
    if ok:
        log("Debian rasmi installed.")
    else:
        err("Install failed.")
    return ok


def install_ubuntu_official():
    step("Ubuntu Official Kernel")
    apt_update()
    ok = apt_install("linux-generic", "linux-headers-generic")
    if ok:
        log("Ubuntu rasmi installed.")
    else:
        err("Install failed.")
    return ok


def install_ubuntu_mainline():
    step("Ubuntu Mainline Kernel")
    apt_update()
    apt_install("software-properties-common")

    rc, _, _ = run("command -v mainline", capture=True)
    if rc != 0:
        run("add-apt-repository -y ppa:cappelikan/ppa", capture=True)
        apt_update()
        apt_install("mainline")

    rc, _, errmsg = run("mainline --install-latest", capture=True)
    if rc == 0:
        log("Mainline installed.")
        return True
    err(f"Mainline error: {errmsg[:200]}")
    return False


# ============================================================
#  PROFILES
# ============================================================
def write_profile(name, body):
    content = (
        f"# ============================================================\n"
        f"#  Profile: {name}\n"
        f"#  Generated: {datetime.now().isoformat()}\n"
        f"#  By: Kernel Tuner v2.1 (Python Edition)\n"
        f"# ============================================================\n\n"
        f"{body}\n"
    )
    SYSCTL_DIR.mkdir(parents=True, exist_ok=True)
    PROFILE_FILE.write_text(content)
    run("sysctl --system", capture=True)
    log(f"Profile '{name}' saved and loaded.")


PROFILES = {
    "STREAMING": """
# --- Congestion ---
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr

# --- Buffers bozorg baraye 4K/8K ---
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.core.rmem_default = 262144
net.core.wmem_default = 262144
net.ipv4.tcp_rmem = 4096 87380 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728
net.ipv4.udp_rmem_min = 8192
net.ipv4.udp_wmem_min = 8192

# --- Paydari ---
net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_notsent_lowat = 131072
net.ipv4.tcp_mtu_probing = 1
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_ecn = 1
net.ipv4.tcp_window_scaling = 1
net.ipv4.tcp_timestamps = 1
net.ipv4.tcp_sack = 1

# --- Connections ---
net.ipv4.tcp_max_syn_backlog = 8192
net.core.somaxconn = 8192
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_tw_reuse = 1

# --- Device ---
net.core.netdev_max_backlog = 16384
net.ipv4.tcp_pacing_ca_ratio = 110
net.ipv4.tcp_pacing_ss_ratio = 200
""",

    "GAMING": """
net.core.default_qdisc = fq_codel
net.ipv4.tcp_congestion_control = bbr

net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216

net.ipv4.tcp_low_latency = 1
net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_notsent_lowat = 16384
net.ipv4.tcp_mtu_probing = 1
net.ipv4.tcp_timestamps = 0

net.ipv4.tcp_max_syn_backlog = 4096
net.core.somaxconn = 4096
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_keepalive_time = 120
net.ipv4.tcp_keepalive_intvl = 15
net.ipv4.tcp_keepalive_probes = 3
net.ipv4.tcp_tw_reuse = 1

net.core.netdev_max_backlog = 8192
net.ipv4.tcp_pacing_ca_ratio = 90
net.ipv4.tcp_pacing_ss_ratio = 150
""",

    "DOWNLOAD": """
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr

net.core.rmem_max = 268435456
net.core.wmem_max = 268435456
net.ipv4.tcp_rmem = 4096 131072 268435456
net.ipv4.tcp_wmem = 4096 131072 268435456

net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_notsent_lowat = 262144
net.ipv4.tcp_mtu_probing = 1
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_window_scaling = 1
net.ipv4.tcp_moderate_rcvbuf = 1

net.ipv4.tcp_max_syn_backlog = 16384
net.core.somaxconn = 16384
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_tw_reuse = 1

net.core.netdev_max_backlog = 32768
net.ipv4.tcp_pacing_ca_ratio = 120
net.ipv4.tcp_pacing_ss_ratio = 200
""",

    "BROWSING": """
net.core.default_qdisc = fq_codel
net.ipv4.tcp_congestion_control = bbr

net.core.rmem_max = 33554432
net.core.wmem_max = 33554432
net.ipv4.tcp_rmem = 4096 87380 33554432
net.ipv4.tcp_wmem = 4096 65536 33554432

net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_notsent_lowat = 65536
net.ipv4.tcp_mtu_probing = 1

net.ipv4.tcp_max_syn_backlog = 8192
net.core.somaxconn = 8192
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_tw_reuse = 1

net.core.netdev_max_backlog = 8192
net.ipv4.tcp_pacing_ca_ratio = 110
net.ipv4.tcp_pacing_ss_ratio = 200
""",

    "BALANCED": """
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr

net.core.rmem_max = 67108864
net.core.wmem_max = 67108864
net.ipv4.tcp_rmem = 4096 87380 67108864
net.ipv4.tcp_wmem = 4096 65536 67108864

net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_notsent_lowat = 131072
net.ipv4.tcp_mtu_probing = 1
net.ipv4.tcp_ecn = 1
net.ipv4.tcp_window_scaling = 1

net.ipv4.tcp_max_syn_backlog = 8192
net.core.somaxconn = 8192
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_tw_reuse = 1

net.core.netdev_max_backlog = 16384
net.ipv4.tcp_pacing_ca_ratio = 110
net.ipv4.tcp_pacing_ss_ratio = 200
""",
}


def apply_profile(name):
    if name not in PROFILES:
        err(f"Profile '{name}' does not exist.")
        return
    step(f"Profile: {name}")
    write_profile(name, PROFILES[name])


def apply_custom_profile():
    print(f"\n{C.CY}{C.BD}              CUSTOM PROFILE MODE{C.N}")
    hr2()
    print(f"\n{C.Y}  Guide:{C.N}")
    print(f"    {C.DM}•{C.N} Har meghdar ro vared kon ya Enter bezan ta pishfarz bemune.")
    print(f"    {C.DM}•{C.N} Byte ha: 134217728 = 128MB  |  268435456 = 256MB")
    print()

    def ask(prompt, default):
        val = input(f"  {prompt} [{C.DM}{default}{C.N}]: ").strip()
        return val or default

    print(f"{C.DM}  ─── Congestion ───{C.N}")
    cc = ask("tcp_congestion_control", "bbr")
    qd = ask("default_qdisc", "fq")

    print(f"{C.DM}  ─── Buffers (byte) ───{C.N}")
    rm = ask("rmem_max", "134217728")
    wm = ask("wmem_max", "134217728")

    print(f"{C.DM}  ─── Tuning ───{C.N}")
    nl = ask("tcp_notsent_lowat", "131072")
    mt = ask("tcp_mtu_probing", "1")
    fo = ask("tcp_fastopen", "3")
    ss = ask("tcp_slow_start_after_idle", "0")
    ec = ask("tcp_ecn", "1")
    tw = ask("tcp_tw_reuse", "1")
    ft = ask("tcp_fin_timeout", "30")

    print(f"{C.DM}  ─── Connections ───{C.N}")
    sc = ask("somaxconn", "8192")
    sb = ask("tcp_max_syn_backlog", "8192")
    nb = ask("netdev_max_backlog", "16384")

    body = f"""
net.core.default_qdisc = {qd}
net.ipv4.tcp_congestion_control = {cc}

net.core.rmem_max = {rm}
net.core.wmem_max = {wm}
net.ipv4.tcp_rmem = 4096 87380 {rm}
net.ipv4.tcp_wmem = 4096 65536 {wm}

net.ipv4.tcp_slow_start_after_idle = {ss}
net.ipv4.tcp_fastopen = {fo}
net.ipv4.tcp_notsent_lowat = {nl}
net.ipv4.tcp_mtu_probing = {mt}
net.ipv4.tcp_ecn = {ec}
net.ipv4.tcp_window_scaling = 1
net.ipv4.tcp_sack = 1
net.ipv4.tcp_tw_reuse = {tw}
net.ipv4.tcp_fin_timeout = {ft}

net.ipv4.tcp_max_syn_backlog = {sb}
net.core.somaxconn = {sc}
net.ipv4.ip_local_port_range = 1024 65535

net.core.netdev_max_backlog = {nb}
"""
    write_profile("CUSTOM", body)


# ============================================================
#  BACKUP / RESTORE
# ============================================================
def backup_existing():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    if PROFILE_FILE.exists():
        shutil.copy2(PROFILE_FILE, BACKUP_DIR / PROFILE_FILE.name)
        info(f"Backup: {BACKUP_DIR}")


def restore_backup():
    backups = sorted(
        SYSCTL_DIR.glob("backup-*"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not backups:
        warn("No backup found.")
        return
    last = backups[0]
    src = last / PROFILE_FILE.name
    if src.exists():
        shutil.copy2(src, PROFILE_FILE)
        run("sysctl --system", capture=True)
        log(f"Restored from: {last}")
    else:
        warn(f"Profile file in {last} not found.")


# ============================================================
#  STATUS
# ============================================================
def get_running_kernel():
    rc, out, _ = run("uname -r", capture=True)
    return out if rc == 0 else "?"


def get_installed_kernels():
    rc, out, _ = run(
        "dpkg-query -W -f='${Package}\\n' 'linux-image-*' 2>/dev/null | "
        "grep -vE 'linux-image-(generic|amd64|virtual|unsigned|cloud|lowlatency|aws|azure|gcp|gke|kvm|oracle|raspi|snapd)' | "
        "sort -V",
        capture=True,
    )
    if rc != 0 or not out:
        return []
    return [l.strip() for l in out.splitlines() if l.strip()]


def get_boot_kernel():
    rc, out, _ = run("grep -m1 '^linux ' /boot/grub/grub.cfg 2>/dev/null | "
                     "sed -E 's/.*vmlinuz-([^ ]+).*/\\1/'", capture=True)
    return out if rc == 0 and out else "?"


def show_status():
    os.system("clear")
    hr2()
    print(f"{C.CY}{C.BD}              KERNEL STATUS{C.N}")
    hr2()
    print()

    running   = get_running_kernel()
    boot_next = get_default_boot_kernel()
    installed = get_installed_kernels()

    print(f"  {C.W}{'Running kernel:':<22}{C.N} {C.G}{running}{C.N}")
    print(f"  {C.W}{'Next boot kernel:':<22}{C.N} {C.G}{boot_next}{C.N}")

    if boot_next != "?" and running != boot_next:
        verdict = f"{C.Y}CHANGED - reboot to activate{C.N}"
    elif boot_next == "?":
        verdict = f"{C.DM}unknown (no grub.cfg){C.N}"
    else:
        verdict = f"{C.G}no change{C.N}"
    print(f"  {C.W}{'Status:':<22}{C.N} {verdict}")
    print()

    if installed:
        print(f"  {C.W}Installed kernels:{C.N}")
        for k in installed:
            tags = []
            if k == running:
                tags.append(f"{C.G}[running]{C.N}")
            if k == boot_next:
                tags.append(f"{C.Y}[next boot]{C.N}")
            tag = " ".join(tags)
            print(f"    {C.DM}*{C.N} {k}  {tag}")
        print()

    print(f"  {C.DM}-- sysctl --{C.N}")
    fields = [
        ("Congestion",     "sysctl -n net.ipv4.tcp_congestion_control"),
        ("Qdisc",          "sysctl -n net.core.default_qdisc"),
        ("rmem_max",       "sysctl -n net.core.rmem_max"),
        ("wmem_max",       "sysctl -n net.core.wmem_max"),
        ("netdev_backlog", "sysctl -n net.core.netdev_max_backlog"),
        ("somaxconn",      "sysctl -n net.core.somaxconn"),
    ]
    for label, cmd in fields:
        rc, out, _ = run(cmd, capture=True)
        val = out if rc == 0 and out else "?"
        print(f"  {C.W}{label:<18}{C.N} {C.G}{val}{C.N}")

    print()
    if PROFILE_FILE.exists():
        print(f"  {C.DM}File:{C.N} {PROFILE_FILE}")
    hr2()
    pause()

def show_banner():
    os.system("clear")
    running = get_running_kernel()
    print(f"{C.M}{C.BD}")
    print("""
  +==========================================================+
  |                                                          |
  |        K E R N E L   T U N E R                           |
  |              +   P R O F I L E   M A N A G E R           |
  |                                                          |
  |                 Python Edition  v2.1                     |
  |                                                          |
  +==========================================================+
""")
    print(f"{C.N}")
    print(f"{C.DM}{'-' * 62}{C.N}")

def show_profile_help():
    os.system("clear")
    hr2()
    print(f"{C.CY}{C.BD}              PROFILE HELP{C.N}")
    hr2()
    print()
    helps = [
        ("1) STREAMING", "YouTube / Instagram / Twitch / Netflix",
         "Buffers 128MB • BBR + fq • 1080p/4K bedoone buffering",
         "FRP pishnahadi: pool_count = 10-20"),
        ("2) GAMING", "CS / Valorant / Dota",
         "Buffers 16MB • fq_codel + BBR • tcp_low_latency=1",
         "Timestamps off baraye overhead kamtar"),
        ("3) DOWNLOAD", "Torrent / ISO / bulk transfer",
         "Buffers 256MB • Max throughput • backlog 32768",
         ""),
        ("4) BROWSING", "Everyday web / WiFi / 4G",
         "Buffers 32MB • Masraf RAM kam",
         ""),
        ("5) BALANCED", "Default, hame kar (recommended)",
         "Buffers 64MB • Set & forget",
         ""),
        ("6) CUSTOM", "Hame meghdar dasti",
         "Guide dar har marhale",
         ""),
    ]
    for title, sub, line1, line2 in helps:
        print(f"  {C.G}{C.BD}{title}{C.N}  {C.DM}{sub}{C.N}")
        print(f"      {line1}")
        if line2:
            print(f"      {C.DM}{line2}{C.N}")
        print()
    hr2()
    pause()


# ============================================================
#  MENU: KERNEL
# ============================================================
def menu_kernel(distro_pretty, karch):
    while True:
        os.system("clear")
        hr2()
        print(f"{C.CY}{C.BD}                KERNEL SELECTION{C.N}")
        hr2()
        running = get_running_kernel()
        print(f"  {C.W}Distro:{C.N}  {C.G}{distro_pretty}{C.N}    "
              f"{C.W}Arch:{C.N} {C.G}{karch}{C.N}")
        print(f"  {C.W}Running kernel:{C.N} {C.G}{get_running_kernel()}{C.N}")
        hr()
        print()
        opts = [
            ("1", "XanMod (LTS)",    "Recommended — stable + BBRv3"),
            ("2", "XanMod (MAIN)",   "Newest mainline XanMod"),
            ("3", "XanMod (EDGE)",   "Close to mainline + tweaks"),
            ("4", "XanMod (RT)",     "Real-time for special workloads"),
            ("5", "Liquorix",        "Low latency, desktop, Ubuntu-native"),
            ("6", "Debian Official", "linux-image-amd64"),
            ("7", "Ubuntu Official", "linux-generic"),
            ("8", "Ubuntu Mainline", "Latest kernel from PPA"),
            ("9", "Profile only",  "Without kernel install"),
        ]
        for k, name, desc in opts:
            print(f"   {C.G}{C.BD}{k}){C.N}  {name:<20} {C.DM}{desc}{C.N}")
        hr()
        print(f"   {C.R}{C.BD}C){C.N}  {C.DM}Clean XanMod repo{C.N}")
        print(f"   {C.R}{C.BD}0){C.N}  {C.DM}Exit{C.N}")
        print()
        hr()
        choice = input(f"{C.CY}  Select [0-9/C]: {C.N}").strip().upper()

        if choice == "1":
            install_xanmod("lts"); return
        elif choice == "2":
            install_xanmod("main"); return
        elif choice == "3":
            install_xanmod("edge"); return
        elif choice == "4":
            install_xanmod("rt"); return
        elif choice == "5":
            install_liquorix(); return
        elif choice == "6":
            install_debian_official(); return
        elif choice == "7":
            install_ubuntu_official(); return
        elif choice == "8":
            install_ubuntu_mainline(); return
        elif choice == "9":
            info("Kernel install skipped."); return
        elif choice == "C":
            clean_xanmod()
            pause()
            continue
        elif choice == "0":
            sys.exit(0)
        else:
            err("Invalid choice.")
            time.sleep(1)
            continue


# ============================================================
#  MENU: PROFILE
# ============================================================
def menu_profile():
    while True:
        os.system("clear")
        hr2()
        print(f"{C.CY}{C.BD}                PROFILE SELECTION{C.N}")
        hr2()
        print()
        opts = [
            ("1", "STREAMING", "YouTube / Instagram / Twitch"),
            ("2", "GAMING",    "Low latency"),
            ("3", "DOWNLOAD",  "Max throughput"),
            ("4", "BROWSING",  "Everyday web"),
            ("5", "BALANCED",  "Default"),
            ("6", "CUSTOM",    "Enter manually"),
        ]
        for k, name, desc in opts:
            print(f"   {C.G}{C.BD}{k}){C.N}  {name:<12} {C.DM}{desc}{C.N}")
        hr()
        print(f"   {C.Y}{C.BD}7){C.N}  {C.DM}Guide (profiles explained){C.N}")
        print(f"   {C.Y}{C.BD}8){C.N}  {C.DM}Status current{C.N}")
        print(f"   {C.Y}{C.BD}9){C.N}  {C.DM}Restore backup akhar{C.N}")
        print(f"   {C.R}{C.BD}0){C.N}  {C.DM}Exit{C.N}")
        print()
        hr()
        choice = input(f"{C.CY}  Select [0-9]: {C.N}").strip()

        if choice == "1":
            apply_profile("STREAMING"); return
        elif choice == "2":
            apply_profile("GAMING"); return
        elif choice == "3":
            apply_profile("DOWNLOAD"); return
        elif choice == "4":
            apply_profile("BROWSING"); return
        elif choice == "5":
            apply_profile("BALANCED"); return
        elif choice == "6":
            apply_custom_profile(); return
        elif choice == "7":
            show_profile_help()
            continue
        elif choice == "8":
            show_status()
            continue
        elif choice == "9":
            restore_backup(); return
        elif choice == "0":
            sys.exit(0)
        else:
            err("Invalid choice.")
            time.sleep(1)
            continue


# ============================================================
#  MAIN
# ============================================================
def main():
    check_root()

    try:
        distro_id, codename, version, pretty = detect_distro()
        karch = check_arch()
        check_network()
    except SystemExit:
        raise
    except Exception as e:
        err(f"Pre-check error: {e}")
        sys.exit(1)

    show_banner()
    backup_existing()

    info(f"Distro: {pretty}  (codename: {codename})")
    info(f"Running kernel: {get_running_kernel()}")
    info(f"Running kernel: {get_running_kernel()}")
    info(f"Running kernel: {get_running_kernel()}")
    cpu_lvl = detect_cpu_level()
    info(f"CPU psABI: x86-64-v{cpu_lvl}")

    if distro_id == "ubuntu" and codename not in XANMOD_SUPPORTED:
        warn(f"Codename '{codename}' dar liste rasm XanMod nist.")
        fb = XANMOD_FALLBACK.get(codename, "bookworm")
        info(f"Fallback: '{fb}' will be used.")

    menu_kernel(pretty, karch)
    print()
    menu_profile()

    print()
    hr2()
    print(f"{C.G}{C.BD}  ✓ TAMOOM SHOD!{C.N}")
    hr2()
    warn("Reboot required for new kernel to take effect.")
    info(f"Backup: {BACKUP_DIR}")
    info(f"Log:    {LOG_FILE}")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{C.Y}  ⚠ Cancelled by user.{C.N}")
        sys.exit(130)
    except Exception as e:
        err(f"Unhandled error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
