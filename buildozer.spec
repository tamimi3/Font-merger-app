[app]

# اسم التطبيق
title = Font Merger

# اسم الحزمة
package.name = com.tamimi3.fontmerger

# نسخة التطبيق
version = 1.0

# مجلد الكود
source.dir = .

# امتدادات الملفات المضمنة
source.include_exts = py,png,jpg,kv,atlas

# المتطلبات (المكتبات)
requirement = python3,kivy,fonttools,pillow,arabic-reshaper,python-bidi,uharfbuzz

# اتجاه الشاشة
orientation = portrait

# وضع الشاشة الكاملة
fullscreen = 0

# الأذونات المطلوبة (للوصول إلى التخزين)
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,INTERNET

# الحد الأدنى لنسخة الأندرويد
android.api = 33

# مستوى NDK
android.ndk = 25

# سجل البناء
log_level = 2

# لا تستخدم presplash أو أيقونة افتراضية
presplash.filename = 
icon.filename = 

[buildozer]

# تجاهل بعض الملفات
ignore_pattern = CVS, .*, *.pyc, *.pyo, __pycache__

[cython]
language_level = 3
