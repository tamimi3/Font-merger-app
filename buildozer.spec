[app]
title = Font Merger
package.name = fontmerger
package.domain = org.example
source.dir = .
source.include_exts = py,kv,ttf,otf,png,jpg
version = 0.1
orientation = portrait
android.arch = armeabi-v7a, arm64-v8a

# Requirements: اضبط النسخ حسب حاجتك. fonttools بالاسم الصغير.
requirements = python3,kivy==2.1.0,fonttools

# أذونات
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# API / SDK / NDK — قيم شائعة تعمل عادةً
android.api = 33
android.minapi = 21
android.sdk = 33
android.ndk = 23b
android.ndk_api = 21

# استخدم فرع حديث من python-for-android إذا احتجت
p4a.branch = master

# logging
log_level = 2
