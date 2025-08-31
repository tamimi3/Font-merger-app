[app]

# (str) Title of your application
title = Font Merger

# (str) Package name
package.name = fontmerger

# (str) Package domain (needed for android/ios packaging)
package.domain = com.example

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas

# (list) List of inclusions using pattern matching
#source.include_patterns = assets/*,images/*.png

# (list) Source files to exclude (let empty to not exclude anything)
source.exclude_exts = spec

# (list) List of directory to exclude (let empty to not exclude anything)
source.exclude_dirs = tests, bin, venv

# (list) List of exclusions using pattern matching
#source.exclude_patterns = license,images/*/*.jpg

# (str) Application versioning (method 1)
version = 0.1

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy,fonttools  # أضف fonttools إذا لم يكن موجوداً

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/icon.png

# (list) Permissions
permissions = android.permission.READ_EXTERNAL_STORAGE,android.permission.WRITE_EXTERNAL_STORAGE  # إضافة الإذونات هنا

# (int) Target Android SDK
android.sdk = 33  # حدث لدعم Android حديث

# (int) Minimum API your APK will support
android.minapi = 21

# (int) Android API that you want to use
android.api = 33

# (bool) Indicate whether the package should be debuggable or not
android.debuggable = True

# (str) Android logcat filters to use
android.logcat_filters = *:S python:D
