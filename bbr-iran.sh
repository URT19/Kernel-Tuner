#!/bin/bash

#### how to run --------------------------------------------------------------
### wget https://github.com/URT19/Kernel-Tuner/raw/refs/heads/main/bbr-iran.sh
## chmod +x bbr-iran.sh
# sudo bash bbr-iran.sh


# BBR Optimization for Iranian Internet
# High latency + packet loss friendly

set -e

echo "=== Optimizing BBR for Iranian Network Conditions ==="

# Load BBR module
modprobe tcp_bbr 2>/dev/null || true
echo "tcp_bbr" > /etc/modules-load.d/bbr.conf

# Create optimized config
cat > /etc/sysctl.d/99-bbr-iran.conf << 'EOF'
# ============================================
# BBR Optimized for Iranian Internet
# High Latency + Packet Loss
# ============================================

# --- Congestion Control ---
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr

# --- TCP Buffers (مناسب تأخیر بالا) ---
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.core.rmem_default = 262144
net.core.wmem_default = 262144
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216

# --- مهم برای اینترنت ایران ---
net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_mtu_probing = 1
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_no_metrics_save = 1

# --- کاهش تأثیر پکت‌لاس ---
net.ipv4.tcp_sack = 1
net.ipv4.tcp_dsack = 1
net.ipv4.tcp_fack = 1
net.ipv4.tcp_window_scaling = 1

# --- Network Stack ---
net.core.netdev_max_backlog = 5000
net.core.somaxconn = 1024
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_keepalive_probes = 5
net.ipv4.tcp_keepalive_intvl = 15

# --- Memory ---
vm.swappiness = 10
vm.dirty_ratio = 10
vm.dirty_background_ratio = 5
EOF

# Apply
sysctl --system > /dev/null

echo ""
echo "=== Current Status ==="
echo -n "Congestion Control : "
sysctl -n net.ipv4.tcp_congestion_control
echo -n "Default Qdisc      : "
sysctl -n net.core.default_qdisc
echo ""
echo "Optimization applied successfully."
echo "It is recommended to reboot once."
