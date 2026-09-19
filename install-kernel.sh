#!/usr/bin/env bash
# ==========================================================
#  Kernel Installer + Profile Manager (Finglish)
#  Author: Custom
#  Support: Debian 11/12, Ubuntu 20.04/22.04/24.04
# ==========================================================

set -euo pipefail

# ---------- Colors ----------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'
BOLD='\033[1m'

# ---------- Paths ----------
SYSCTL_DIR="/etc/sysctl.d"
PROFILE_DIR="/etc/kernel-profiles"
BACKUP_DIR="/etc/sysctl.d/backup-$(date +%Y%m%d-%H%M%S)"
LOG_FILE="/var/log/kernel-installer.log"

# ---------- Helpers ----------
log()  { echo -e "${GREEN}[+]${NC} $*" | tee -a "$LOG_FILE"; }
warn() { echo -e "${YELLOW}[!]${NC} $*" | tee -a "$LOG_FILE"; }
err()  { echo -e "${RED}[x]${NC} $*" | tee -a "$LOG_FILE"; }
info() { echo -e "${BLUE}[i]${NC} $*" | tee -a "$LOG_FILE"; }

check_root() {
    if [[ $EUID -ne 0 ]]; then
        err "Bayad ba root ejra koni. (sudo bash $0)"
        exit 1
    fi
}

detect_distro() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        DISTRO_ID="$ID"
        DISTRO_VER="$VERSION_ID"
        DISTRO_CODENAME="${VERSION_CODENAME:-}"
    else
        err "OS release file peyda nashod."
        exit 1
    fi

    case "$DISTRO_ID" in
        ubuntu|debian) log "Distro: $PRETTY_NAME" ;;
        *) warn "Distro $DISTRO_ID test nashode, vali edame midim..." ;;
    esac
}

check_arch() {
    ARCH=$(uname -m)
    case "$ARCH" in
        x86_64|amd64) KARCH="amd64" ;;
        aarch64|arm64) KARCH="arm64" ;;
        *) err "Architecture $ARCH support nemishe."; exit 1 ;;
    esac
}

# ==========================================================
#  KERNEL INSTALLATION
# ==========================================================

install_xanmod() {
    log "XanMod Kernel nasb mishe..."

    apt-get update -y
    apt-get install -y wget gnupg ca-certificates

    # GPG key
    wget -qO - https://dl.xanmod.org/archive.key | gpg --dearmor -o /usr/share/keyrings/xanmod-archive-keyring.gpg

    # Repo
    echo 'deb [signed-by=/usr/share/keyrings/xanmod-archive-keyring.gpg] http://deb.xanmod.org releases main' \
        > /etc/apt/sources.list.d/xanmod-release.list

    apt-get update -y

    # Detect best version
    local cpu_level
    cpu_level=$(awk -f <(wget -qO - https://dl.xanmod.org/check_x86-64_psabi.sh) 2>/dev/null || echo "2")

    case "$cpu_level" in
        1) PKG="linux-xanmod-x64v1" ;;
        2) PKG="linux-xanmod-x64v2" ;;
        3) PKG="linux-xanmod-x64v3" ;;
        4) PKG="linux-xanmod-x64v4" ;;
        *) PKG="linux-xanmod" ;;
    esac

    log "Package entekhab shode: $PKG"
    apt-get install -y "$PKG" || apt-get install -y linux-xanmod

    log "XanMod nasb shod. Reboot faramoosh nashe!"
}

install_liquorix() {
    log "Liquorix Kernel nasb mishe..."

    apt-get update -y
    apt-get install -y wget gnupg ca-certificates curl

    curl -s 'https://liquorix.net/install-liquorix.sh' | bash

    log "Liquorix nasb shod."
}

install_zen() {
    log "Zen Kernel nasb mishe..."

    if [[ "$DISTRO_ID" == "ubuntu" ]]; then
        add-apt-repository -y ppa:graysky/utils
        apt-get update -y
        apt-get install -y linux-generic
        warn "Zen rooye Ubuntu az PPA nayad. Be jaye un XanMod ya Liquorix ro entekhab kon."
        warn "Dar Ubuntu mishe zen kernel ro dasti compile kard ke scriptesho joda midim."
    else
        # Debian
        apt-get install -y linux-image-amd64
        warn "Zen rooye Debian rasmi nist. Likely bayad dasti build koni."
    fi
}

install_debian_official() {
    log "Debian Official Kernel nasb mishe..."

    apt-get update -y
    apt-get install -y linux-image-amd64 linux-headers-amd64 firmware-linux

    log "Debian rasmi nasb shod."
}

install_ubuntu_official() {
    log "Ubuntu Official Kernel nasb mishe..."

    apt-get update -y
    apt-get install -y linux-generic linux-headers-generic

    log "Ubuntu rasmi nasb shod."
}

install_mainline_ubuntu() {
    log "Mainline Kernel (Ubuntu) nasb mishe..."

    if ! command -v mainline &>/dev/null; then
        add-apt-repository -y ppa:cappelikan/ppa
        apt-get update -y
        apt-get install -y mainline
    fi

    mainline --install-latest
    log "Mainline nasb shod."
}

# ==========================================================
#  PROFILES
# ==========================================================

apply_streaming_profile() {
    log "Profile: STREAMING (YouTube, Instagram, Twitch, Netflix)"
    cat > "$SYSCTL_DIR/99-kernel-profile.conf" <<'EOF'
# ===== STREAMING PROFILE =====
# Target: high throughput, stable connections, low buffering

# Congestion Control
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr

# Large Buffers (4K/8K streaming)
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.core.rmem_default = 262144
net.core.wmem_default = 262144
net.ipv4.tcp_rmem = 4096 87380 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728
net.ipv4.udp_rmem_min = 8192
net.ipv4.udp_wmem_min = 8192

# TCP tuning for streaming stability
net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_notsent_lowat = 131072
net.ipv4.tcp_mtu_probing = 1
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_ecn = 1
net.ipv4.tcp_window_scaling = 1
net.ipv4.tcp_timestamps = 1
net.ipv4.tcp_sack = 1
net.ipv4.tcp_fack = 1

# Many connections (CDN, multi-thread video)
net.ipv4.tcp_max_syn_backlog = 8192
net.core.somaxconn = 8192
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_max_tw_buckets = 1440000
net.ipv4.tcp_tw_reuse = 1

# Network device
net.core.netdev_max_backlog = 16384
net.core.dev_weight = 64

# BBR advanced
net.ipv4.tcp_pacing_ca_ratio = 110
net.ipv4.tcp_pacing_ss_ratio = 200
EOF
    log "Streaming profile sabt shod."
}

apply_gaming_profile() {
    log "Profile: GAMING (latency kam, packet loss kam)"
    cat > "$SYSCTL_DIR/99-kernel-profile.conf" <<'EOF'
# ===== GAMING PROFILE =====
# Target: ultra low latency, minimal jitter

# Congestion Control
net.core.default_qdisc = fq_codel
net.ipv4.tcp_congestion_control = bbr

# Small buffers = low latency
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.core.rmem_default = 212992
net.core.wmem_default = 212992
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216

# Latency-critical
net.ipv4.tcp_low_latency = 1
net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_notsent_lowat = 16384
net.ipv4.tcp_mtu_probing = 1
net.ipv4.tcp_timestamps = 0
net.ipv4.tcp_sack = 1

# Connection handling
net.ipv4.tcp_max_syn_backlog = 4096
net.core.somaxconn = 4096
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_keepalive_time = 120
net.ipv4.tcp_keepalive_intvl = 15
net.ipv4.tcp_keepalive_probes = 3
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_max_tw_buckets = 262144

# Device
net.core.netdev_max_backlog = 8192
net.core.dev_weight = 64

# BBR aggression
net.ipv4.tcp_pacing_ca_ratio = 90
net.ipv4.tcp_pacing_ss_ratio = 150
EOF
    log "Gaming profile sabt shod."
}

apply_download_profile() {
    log "Profile: DOWNLOAD (throughput max, bulk transfer)"
    cat > "$SYSCTL_DIR/99-kernel-profile.conf" <<'EOF'
# ===== DOWNLOAD PROFILE =====
# Target: maximum throughput for bulk downloads

# Congestion Control
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr

# Very large buffers
net.core.rmem_max = 268435456
net.core.wmem_max = 268435456
net.core.rmem_default = 1048576
net.core.wmem_default = 1048576
net.ipv4.tcp_rmem = 4096 131072 268435456
net.ipv4.tcp_wmem = 4096 131072 268435456

# Bulk transfer
net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_notsent_lowat = 262144
net.ipv4.tcp_mtu_probing = 1
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_window_scaling = 1
net.ipv4.tcp_moderate_rcvbuf = 1

# Many parallel downloads
net.ipv4.tcp_max_syn_backlog = 16384
net.core.somaxconn = 16384
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_max_tw_buckets = 2000000
net.ipv4.tcp_tw_reuse = 1

# Device
net.core.netdev_max_backlog = 32768
net.core.dev_weight = 128

# BBR
net.ipv4.tcp_pacing_ca_ratio = 120
net.ipv4.tcp_pacing_ss_ratio = 200
EOF
    log "Download profile sabt shod."
}

apply_browsing_profile() {
    log "Profile: BROWSING (web, low resource)"
    cat > "$SYSCTL_DIR/99-kernel-profile.conf" <<'EOF'
# ===== BROWSING PROFILE =====
# Target: web browsing, many small connections

# Congestion Control
net.core.default_qdisc = fq_codel
net.ipv4.tcp_congestion_control = bbr

# Balanced buffers
net.core.rmem_max = 33554432
net.core.wmem_max = 33554432
net.ipv4.tcp_rmem = 4096 87380 33554432
net.ipv4.tcp_wmem = 4096 65536 33554432

# Browsing
net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_notsent_lowat = 65536
net.ipv4.tcp_mtu_probing = 1
net.ipv4.tcp_window_scaling = 1
net.ipv4.tcp_sack = 1
net.ipv4.tcp_timestamps = 1

# Connections
net.ipv4.tcp_max_syn_backlog = 8192
net.core.somaxconn = 8192
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_max_tw_buckets = 524288

# Device
net.core.netdev_max_backlog = 8192

# BBR
net.ipv4.tcp_pacing_ca_ratio = 110
net.ipv4.tcp_pacing_ss_ratio = 200
EOF
    log "Browsing profile sabt shod."
}

apply_balanced_profile() {
    log "Profile: BALANCED (default, hame kar)"
    cat > "$SYSCTL_DIR/99-kernel-profile.conf" <<'EOF'
# ===== BALANCED PROFILE =====
# Target: good for everything, no extremes

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
net.ipv4.tcp_window_scaling = 1
net.ipv4.tcp_ecn = 1

net.ipv4.tcp_max_syn_backlog = 8192
net.core.somaxconn = 8192
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_tw_reuse = 1

net.core.netdev_max_backlog = 16384

net.ipv4.tcp_pacing_ca_ratio = 110
net.ipv4.tcp_pacing_ss_ratio = 200
EOF
    log "Balanced profile sabt shod."
}

# ==========================================================
#  CUSTOM MODE
# ==========================================================

apply_custom_profile() {
    clear
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}              CUSTOM PROFILE MODE${NC}"
    echo -e "${CYAN}============================================================${NC}"
    echo ""
    echo -e "${YELLOW}Rahnama:${NC}"
    echo "  - Har meghdar ro mituni vared koni ya Enter bezani ta pishfarz bemune."
    echo "  - Meghdar ha be byte hastan (masalan 134217728 = 128MB)."
    echo "  - Baraye buffer ha, pishnahad mikonim ghabl az taghir, profile mored nazar ro bekhuni."
    echo ""

    read -rp "tcp_congestion_control [bbr] (bbr/cubic/vegas): " CC
    CC=${CC:-bbr}

    read -rp "default_qdisc [fq] (fq/fq_codel/cake): " QDISC
    QDISC=${QDISC:-fq}

    read -rp "tcp_rmem_max (byte) [134217728 = 128MB]: " RMEM
    RMEM=${RMEM:-134217728}

    read -rp "tcp_wmem_max (byte) [134217728 = 128MB]: " WMEM
    WMEM=${WMEM:-134217728}

    read -rp "netdev_max_backlog [16384]: " BACKLOG
    BACKLOG=${BACKLOG:-16384}

    read -rp "somaxconn [8192]: " SOMAX
    SOMAX=${SOMAX:-8192}

    read -rp "tcp_max_syn_backlog [8192]: " SYN
    SYN=${SYN:-8192}

    read -rp "tcp_notsent_lowat [131072]: " NOTSENT
    NOTSENT=${NOTSENT:-131072}

    read -rp "tcp_mtu_probing [1] (0/1/2): " MTU
    MTU=${MTU:-1}

    read -rp "tcp_fastopen [3] (0/1/2/3): " FO
    FO=${FO:-3}

    read -rp "tcp_slow_start_after_idle [0] (0/1): " SS
    SS=${SS:-0}

    read -rp "tcp_ecn [1] (0/1/2): " ECN
    ECN=${ECN:-1}

    read -rp "tcp_tw_reuse [1] (0/1): " TW
    TW=${TW:-1}

    read -rp "tcp_fin_timeout [30]: " FIN
    FIN=${FIN:-30}

    cat > "$SYSCTL_DIR/99-kernel-profile.conf" <<EOF
# ===== CUSTOM PROFILE =====
# Generated: $(date)

net.core.default_qdisc = $QDISC
net.ipv4.tcp_congestion_control = $CC

net.core.rmem_max = $RMEM
net.core.wmem_max = $WMEM
net.ipv4.tcp_rmem = 4096 87380 $RMEM
net.ipv4.tcp_wmem = 4096 65536 $WMEM

net.ipv4.tcp_slow_start_after_idle = $SS
net.ipv4.tcp_fastopen = $FO
net.ipv4.tcp_notsent_lowat = $NOTSENT
net.ipv4.tcp_mtu_probing = $MTU
net.ipv4.tcp_ecn = $ECN
net.ipv4.tcp_window_scaling = 1
net.ipv4.tcp_sack = 1

net.ipv4.tcp_max_syn_backlog = $SYN
net.core.somaxconn = $SOMAX
net.ipv4.ip_local_port_range = 1024 65535
net.ipv4.tcp_tw_reuse = $TW
net.ipv4.tcp_fin_timeout = $FIN

net.core.netdev_max_backlog = $BACKLOG
EOF

    log "Custom profile sabt shod."
}

# ==========================================================
#  APPLY / BACKUP / RESTORE
# ==========================================================

backup_existing() {
    mkdir -p "$BACKUP_DIR"
    if [[ -f "$SYSCTL_DIR/99-kernel-profile.conf" ]]; then
        cp "$SYSCTL_DIR/99-kernel-profile.conf" "$BACKUP_DIR/"
        log "Backup girifte shod: $BACKUP_DIR"
    fi
}

load_profile() {
    sysctl --system >/dev/null 2>&1 || true
    log "Profile load shod."
}

show_current() {
    echo ""
    echo -e "${CYAN}=== Vaziat فعلی ===${NC}"
    echo "Congestion: $(sysctl -n net.ipv4.tcp_congestion_control 2>/dev/null || echo '?')"
    echo "Qdisc:      $(sysctl -n net.core.default_qdisc 2>/dev/null || echo '?')"
    echo "rmem_max:   $(sysctl -n net.core.rmem_max 2>/dev/null || echo '?')"
    echo "wmem_max:   $(sysctl -n net.core.wmem_max 2>/dev/null || echo '?')"
    echo "Backlog:    $(sysctl -n net.core.netdev_max_backlog 2>/dev/null || echo '?')"
    echo ""
    echo -e "${CYAN}=== Kernel فعلی ===${NC}"
    uname -r
    echo ""
}

# ==========================================================
#  MENUS
# ==========================================================

show_profile_help() {
    cat <<'EOF'

================================================================
                    RAHNAMAYE PROFILE HA
================================================================

[1] STREAMING  - Baraye YouTube, Instagram, Twitch, Netflix
    - Buffer haye bozorg (128MB)
    - BBR + fq
    - Suitable baraye 1080p/4K bedoone buffering
    - pool_count pishnahadi dar FRP: 10-20

[2] GAMING     - Baraye game haye online (CS, Valorant, Dota)
    - Buffer haye kuchak, latency kam
    - fq_codel + BBR
    - tcp_low_latency = 1
    - tcp_timestamps = 0 (baraye kam kardan overhead)

[3] DOWNLOAD   - Baraye download hajim (torrent, ISO, bulk)
    - Buffer haye kheili bozorg (256MB)
    - Throughput max
    - netdev_max_backlog = 32768

[4] BROWSING   - Baraye web browsing roozmare
    - Buffer haye motadadel (32MB)
    - Suitable baraye WiFi/4G
    - Masraf RAM kam

[5] BALANCED   - Pishfarz, hame kar (recommended)
    - 64MB buffers
    - BBR + fq
    - Best "set & forget"

[6] CUSTOM     - Vared kardan dasti hame meghdar ha
    - Baraye karbarane herfei
    - Rahnama dar har marhale namayesh dade mishe

================================================================
EOF
}

menu_kernel() {
    clear
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}               KERNEL SELECTION${NC}"
    echo -e "${CYAN}============================================================${NC}"
    echo ""
    echo "  1) XanMod          (takhassosi baraye streaming/gaming)"
    echo "  2) Liquorix        (latency kam, desktop)"
    echo "  3) Zen Kernel      (Debian/Ubuntu - dasti compile)"
    echo "  4) Debian Official (linux-image-amd64)"
    echo "  5) Ubuntu Official (linux-generic)"
    echo "  6) Ubuntu Mainline (jadidtarin kernel)"
    echo "  7) Faghat Profile  (bedoone nasb kernel)"
    echo "  0) Exit"
    echo ""
    read -rp "Entekhab kon [0-7]: " kchoice

    case "$kchoice" in
        1) install_xanmod ;;
        2) install_liquorix ;;
        3) install_zen ;;
        4) install_debian_official ;;
        5) install_ubuntu_official ;;
        6) install_mainline_ubuntu ;;
        7) info "Nasb kernel skip shod." ;;
        0) exit 0 ;;
        *) err "Entekhab namotabar."; menu_kernel ;;
    esac
}

menu_profile() {
    clear
    echo -e "${CYAN}============================================================${NC}"
    echo -e "${CYAN}               PROFILE SELECTION${NC}"
    echo -e "${CYAN}============================================================${NC}"
    echo ""
    echo "  1) STREAMING  (YouTube/Instagram/Twitch)"
    echo "  2) GAMING     (latency kam)"
    echo "  3) DOWNLOAD   (throughput max)"
    echo "  4) BROWSING   (web roozmare)"
    echo "  5) BALANCED   (pishfarz)"
    echo "  6) CUSTOM     (dasti vared kon)"
    echo "  7) Nemayesh rahnama"
    echo "  8) Nemayesh vaziat فعلی"
    echo "  9) Restore az backup akhar"
    echo "  0) Exit"
    echo ""
    read -rp "Entekhab kon [0-9]: " pchoice

    case "$pchoice" in
        1) apply_streaming_profile ;;
        2) apply_gaming_profile ;;
        3) apply_download_profile ;;
        4) apply_browsing_profile ;;
        5) apply_balanced_profile ;;
        6) apply_custom_profile ;;
        7) show_profile_help; read -rp "Enter bezan..." _; menu_profile ;;
        8) show_current; read -rp "Enter bezan..." _; menu_profile ;;
        9) restore_backup ;;
        0) exit 0 ;;
        *) err "Entekhab namotabar."; menu_profile ;;
    esac
}

restore_backup() {
    local last
    last=$(ls -dt /etc/sysctl.d/backup-* 2>/dev/null | head -1 || true)
    if [[ -z "$last" ]]; then
        warn "Hich backup peyda nashod."
        return
    fi
    cp "$last/99-kernel-profile.conf" "$SYSCTL_DIR/" 2>/dev/null || true
    sysctl --system >/dev/null 2>&1 || true
    log "Restore shod az: $last"
}

# ==========================================================
#  MAIN
# ==========================================================

main() {
    check_root
    detect_distro
    check_arch

    clear
    echo -e "${MAGENTA}${BOLD}"
    echo "============================================================"
    echo "        KERNEL INSTALLER + PROFILE MANAGER"
    echo "        Finglish Edition v1.0"
    echo "============================================================"
    echo -e "${NC}"

    backup_existing

    menu_kernel
    echo ""
    menu_profile

    load_profile
    show_current

    echo ""
    log "Tamoom shod!"
    warn "Baraye asar kardane kamel kernel jadid, system ro reboot kon."
    warn "Backup: $BACKUP_DIR"
}

main "$@"