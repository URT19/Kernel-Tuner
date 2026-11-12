# Kernel Installer + Profile Manager

### آپدیت به آخرین نسخه بصورت دستی



```
apt update
```


##### نصب کرنل HWE

```
apt install --install-recommends linux-generic-hwe-24.04 -y
```


##### به‌روزرسانی GRUB و ساخت Initramfs

```
update-initramfs -u -k all
update-grub
```

##### بررسی نهایی قبل از راه‌اندازی مجدد

```
echo "===== CURRENT KERNEL ====="
uname -r

echo "===== INSTALLED KERNELS ====="
ls /lib/modules/

echo "===== BOOT IMAGES ====="
ls /boot/vmlinuz-*

echo "===== PACKAGE HEALTH ====="
dpkg --audit

echo "===== APT HEALTH ====="
apt-get check
```

----------------


### پاکسازی کرنل

##### حذف پکیج‌های کرنل XanMod یا نسخه‌های قدیمی
```
sudo apt purge linux-image-7.3.4-x64v3-xanmod1 linux-headers-7.3.4-x64v3-xanmod1
```

##### پاکسازی پکیج‌های یتیم و اضافی (Autoremove)


```
sudo apt autoremove --purge
```

##### به‌روزرسانی نهایی گراب


```
sudo update-grub
```
---------
### بهینه سازی پینگ و سرعت

```
nano t1
```


```
#!/bin/bash

# ============================================
# Low Latency / Low Ping Optimization Script
# ============================================

set -e

BACKUP_DIR="/root/lowping-backup-$(date +%Y%m%d-%H%M%S)"
SYSCTL_FILE="/etc/sysctl.d/99-low-ping.conf"
GOVERNOR_SERVICE="/etc/systemd/system/cpu-performance.service"

echo "=== Low Ping Optimization Script ==="
echo ""

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root."
   exit 1
fi

mkdir -p "$BACKUP_DIR"
echo "[+] Backup directory: $BACKUP_DIR"

# Backup
sysctl -a > "$BACKUP_DIR/sysctl-before.conf" 2>/dev/null || true
cp /etc/sysctl.conf "$BACKUP_DIR/" 2>/dev/null || true
cp -r /etc/sysctl.d/ "$BACKUP_DIR/sysctl.d/" 2>/dev/null || true

# 1. Enable BBR + fq
echo "[1/4] Enabling BBR and fq..."

modprobe tcp_bbr 2>/dev/null || true
echo "tcp_bbr" > /etc/modules-load.d/bbr.conf

cat > "$SYSCTL_FILE" << 'EOF'
# Low Latency / Low Ping Optimizations

net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr

net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.core.rmem_default = 262144
net.core.wmem_default = 262144
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216

net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_slow_start_after_idle = 0
net.ipv4.tcp_no_metrics_save = 1
net.ipv4.tcp_moderate_rcvbuf = 1

net.core.netdev_max_backlog = 5000
net.core.somaxconn = 1024
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_keepalive_probes = 5
net.ipv4.tcp_keepalive_intvl = 15

vm.swappiness = 10
vm.dirty_ratio = 10
vm.dirty_background_ratio = 5
EOF

sysctl --system > /dev/null 2>&1
echo "   Done"

# 2. CPU Governor
echo "[2/4] Setting CPU governor to performance..."

if command -v cpupower >/dev/null 2>&1; then
    cpupower frequency-set -g performance >/dev/null 2>&1 || true
else
    for gov in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
        echo performance > "$gov" 2>/dev/null || true
    done
fi

cat > "$GOVERNOR_SERVICE" << 'EOF'
[Unit]
Description=Set CPU Governor to Performance
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'if command -v cpupower >/dev/null; then cpupower frequency-set -g performance; else for g in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do echo performance > $g; done; fi'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now cpu-performance.service >/dev/null 2>&1 || true
echo "   Done"

# 3. Transparent Huge Pages
echo "[3/4] Configuring Transparent Huge Pages..."
echo never > /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null || true
echo never > /sys/kernel/mm/transparent_hugepage/defrag 2>/dev/null || true
echo "   Done"

# 4. Status
echo ""
echo "[4/4] Current status:"
echo "----------------------------------------"
echo -n "Congestion Control : "
sysctl -n net.ipv4.tcp_congestion_control
echo -n "Default Qdisc      : "
sysctl -n net.core.default_qdisc
echo -n "CPU Governor       : "
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo "N/A (common on VPS)"
echo "----------------------------------------"
echo ""
echo "Optimization completed successfully."
echo "Backup saved in: $BACKUP_DIR"
echo "It is recommended to reboot the system."
```



```
chmod +x t1
sudo bash t1
```



بعد از ریبوت دوباره وضعیت را چک کن:

```
sysctl net.ipv4.tcp_congestion_control
sysctl net.core.default_qdisc
```


----------

## در حال تست می باشد.
در حال حاظر فقط نسخه پایتون اوکی هست 
روی اوبونتو 22 و 24 تست گرفتم اوکی هست.
<div align="center">
<img width="841" height="608" alt="image" src="https://github.com/user-attachments/assets/ebe4bb36-395e-4a62-9126-e8f1bc3b04cd" />


</div>


**ابزار نصب کرنل و تنظیم پروفایل شبکه (Finglish Edition)**

یک اسکریپت ساده و قدرتمند برای نصب کرنل‌های بهینه‌شده و تنظیم پارامترهای `sysctl` شبکه روی Debian و Ubuntu.

---

## ویژگی‌ها

- نصب آسان کرنل‌های محبوب:
  - **XanMod** (بهینه برای Streaming و Gaming)
  - **Liquorix** (کم‌تأخیر، مناسب دسکتاپ)
  - **Zen Kernel**
  - **Debian Official**
  - **Ubuntu Official**
  - **Ubuntu Mainline** (آخرین نسخه‌ها)
- ۵ پروفایل آماده + حالت Custom برای تنظیم `sysctl`
- بک‌آپ خودکار قبل از هر تغییر
- رابط کاربری ساده به زبان **Finglish**
- پشتیبانی از معماری‌های `amd64` و `arm64`
- لاگ کامل در `/var/log/kernel-installer.log`

---

## پروفایل‌های موجود

| پروفایل     | کاربرد                              | ویژگی اصلی                          |
|-------------|-------------------------------------|-------------------------------------|
| **STREAMING** | یوتیوب، اینستاگرام، توییچ، نتفلیکس | بافر بزرگ (۱۲۸ مگابایت) + BBR + fq |
| **GAMING**    | بازی‌های آنلاین (CS، Valorant، Dota) | تأخیر خیلی کم + fq_codel           |
| **DOWNLOAD**  | دانلود حجیم، تورنت، ISO             | حداکثر Throughput (۲۵۶ مگابایت)    |
| **BROWSING**  | وب‌گردی روزمره                      | متعادل و کم‌مصرف                    |
| **BALANCED**  | استفاده عمومی (پیشنهادی)            | بهترین حالت کلی                     |
| **CUSTOM**    | تنظیم دستی همه پارامترها            | برای کاربران حرفه‌ای                |

---

## پیش‌نیازها

- سیستم‌عامل: **Debian 11/12** یا **Ubuntu 20.04 / 22.04 / 24.04**
- دسترسی root (`sudo`)
- اتصال به اینترنت

---

## نصب و اجرا

### روش ۱: اجرای مستقیم (پیشنهادی)

کافیه این دستور رو در ترمینال بزنید:


ترجیحا پیشنهاد میدم دستورات رو توی tmux اجرا کنید تا وسط تعویض کرنل اگه ارتباطتون با سرور قطع شد، اسکریپت نصاب کرنل کارش رو اتمام کنه

```
tmux new -s kernel-changer
```
#### XAN-MOD Python Instalelr

```bash
sudo bash -c 'curl -fsSL https://raw.githubusercontent.com/URT19/Kernel-Tuner/refs/heads/main/kernel-tuner.py -o /tmp/kt.py && python3 /tmp/kt.py'
```



#### UNDER DEVELOPMENT
```bash
sudo bash <(curl -sL https://raw.githubusercontent.com/URT19/Kernel-Tuner/refs/heads/main/install-kernel.sh)
```




### روش ۲: دانلود و سپس اجرا

```bash
# دانلود اسکریپت
curl -sL -o install-kernel.sh https://raw.githubusercontent.com/URT19/Kernel-Tuner/refs/heads/main/install-kernel.sh

# دادن دسترسی اجرا
chmod +x install-kernel.sh

# اجرا با دسترسی root
sudo bash install-kernel.sh
```

### روش ۳: کلون کردن کل مخزن

```bash
git clone https://github.com/URT19/Kernel-Tuner.git
cd Kernel-Tuner
# sudo bash install-kernel.sh
sudo python3 kernel-tuner.py
```

> **نکته:** بعد از اجرای اسکریپت، منوها به صورت تعاملی نمایش داده می‌شوند. ابتدا کرنل و سپس پروفایل را انتخاب کنید.

---

## نحوه استفاده

بعد از اجرای اسکریپت:

1. ابتدا منوی **نصب کرنل** نمایش داده می‌شود.
2. کرنل مورد نظر را انتخاب کنید (یا گزینه ۷ برای فقط تنظیم پروفایل).
3. سپس منوی **انتخاب پروفایل** ظاهر می‌شود.
4. پروفایل دلخواه را انتخاب کنید.
5. بعد از اتمام، سیستم را **ری‌استارت** کنید تا کرنل جدید فعال شود.

### منوی کرنل

```
1) XanMod
2) Liquorix
3) Zen Kernel
4) Debian Official
5) Ubuntu Official
6) Ubuntu Mainline
7) فقط پروفایل (بدون نصب کرنل)
0) خروج
```

### منوی پروفایل

```
1) STREAMING
2) GAMING
3) DOWNLOAD
4) BROWSING
5) BALANCED
6) CUSTOM
7) نمایش راهنما
8) نمایش وضعیت فعلی
9) بازگردانی از آخرین بک‌آپ
0) خروج
```

---

## ساختار پروژه

```
Kernel-Tuner/
├── install-kernel.sh      # اسکریپت اصلی
├── profiles/              # فایل‌های پروفایل (اختیاری)
│   ├── balanced.conf
│   ├── browsing.conf
│   ├── download.conf
│   └── gaming.conf
└── README.md
```

---

## بک‌آپ و بازیابی

قبل از هر تغییر، اسکریپت به‌طور خودکار از فایل تنظیمات فعلی بک‌آپ می‌گیرد:

```
/etc/sysctl.d/backup-YYYYMMDD-HHMMSS/
```

برای بازگردانی آخرین بک‌آپ، از گزینه ۹ در منوی پروفایل استفاده کنید.

---

## نکات مهم

- بعد از نصب کرنل جدید حتماً سیستم را **ری‌استارت** کنید.
- پروفایل‌ها در مسیر زیر ذخیره می‌شوند:
  ```
  /etc/sysctl.d/99-kernel-profile.conf
  ```
- برای مشاهده وضعیت فعلی شبکه و کرنل، از گزینه ۸ استفاده کنید.
- در حالت Custom می‌توانید تمام پارامترهای مهم را دستی وارد کنید.

---

## پشتیبانی

- Debian 11 / 12
- Ubuntu 20.04 / 22.04 / 24.04
- معماری‌های `x86_64` و `aarch64`

---

## مجوز

این پروژه آزاد است. می‌توانید آزادانه استفاده، تغییر و توزیع کنید.

[پروژه xanmod kernel](https://xanmod.org/)  [Gitlab](https://gitlab.com/xanmod/linux)
---

**ساخته‌شده با عشق برای جامعه لینوکس فارسی**  
اگر این ابزار براتون مفید بود، ستاره بدید!
```
