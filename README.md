# Kernel Installer + Profile Manager


## در حال تست می باشد.


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


#### UNDER DEVELOPMENT
```bash
sudo bash <(curl -sL https://raw.githubusercontent.com/URT19/Kernel-Tuner/refs/heads/main/install-kernel.sh)
```


#### XAN-MOD Python Instalelr

```bash
sudo python3 <(curl -sL https://raw.githubusercontent.com/URT19/Kernel-Tuner/refs/heads/main/kernel-tuner.py)
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

---

**ساخته‌شده با عشق برای جامعه لینوکس فارسی**  
اگر این ابزار براتون مفید بود، ستاره بدید!
```
