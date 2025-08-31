[app]
title = Font Merger
package.name = com.tamimi3.fontmerger
version = 1.0
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,otf
requirements = python3,kivy,fonttools,pillow,arabic-reshaper,python-bidi,uharfbuzz
orientation = portrait
fullscreen = 0
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,INTERNET
android.api = 33
android.ndk = 25
log_level = 2
presplash.filename = 
icon.filename = 

[buildozer]
ignore_pattern = CVS, .*, *.pyc, *.pyo, __pycache__

[cython]
language_level = 3
