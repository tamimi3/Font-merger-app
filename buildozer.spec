[app]
# (تعديل عام)
title = Font Merger
package.name = fontmerger
package.domain = org.example
source.dir = .
source.include_exts = py,kv,ttf,otf,png,jpg
version = 0.1
orientation = portrait
android.arch = armeabi-v7a, arm64-v8a

# أهم: ضع الحزم التي يحتاجها التطبيق
requirements = python3,kivy,fonttools

# أذونات: للقراءة/الكتابة على الذاكرة الخارجية (Android 6+ بحاجة لطلب وقت التشغيل أيضاً)
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE

# تأكد من API مناسبة (يمكن تعديلها حسب حاجتك)
android.api = 33
android.minapi = 21
android.sdk = 33
# لمنع مشكلات توقيع أو ndk
# (يمكن تعديل android.ndk/ndk-api لو احتجت)
# p4a.branch = stable

# تضمين ملفات الخطوط إن كنت تريد حزمها داخل الـAPK (اختياري)
#android.add_jar = 

# إعدادات أخرى مفيدة
log_level = 2
# (إن أردت ملفات أكبر ضع android.release = 1 عند الإصدار)
