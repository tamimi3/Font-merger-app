#!/usr/bin/env python3
"""
دمج الخطوط مع معاينة عالية الجودة
Font merger with high-quality preview
"""

import os
import sys
import subprocess
import time
import traceback
import shutil
import tempfile
from fontTools.ttLib import TTFont
try:
    from fontTools.varLib.instancer import instantiateVariableFont
except Exception:
    try:
        from fontTools.varLib.mutator import instantiateVariableFont
    except Exception:
        instantiateVariableFont = None

from fontTools.merge import Merger
from fontTools.subset import main as subset_main
from PIL import Image, ImageDraw, ImageFont, features
import arabic_reshaper
from bidi.algorithm import get_display

# محاولة استيراد harfbuzz و uharfbuzz
try:
    import harfbuzz as hb
except ImportError:
    try:
        import uharfbuzz as hb
    except ImportError:
        hb = None

# ======= تعديل مسار التخزين الخارجي ليتوافق مع الأندرويد أو سطح المكتب =======
def get_storage_path():
    try:
        from android.storage import primary_external_storage_path
        return primary_external_storage_path()
    except ImportError:
        return os.path.expanduser("~")

STORAGE_ROOT = get_storage_path()
FONT_DIR = os.path.join(STORAGE_ROOT, "fonts")
TEMP_DIR = os.path.join(FONT_DIR, "temp_processing")
# ============================================================================

EN_PREVIEW = "The quick brown fox jumps over the lazy dog. 1234567890"
AR_PREVIEW = "سمَات مجانية، إختر مِنْ بين أكثر من ١٠٠ سمة مجانية او انشئ سماتك الخاصة هُنا في هذا التطبيق النظيف ..."

# إنشاء المجلد المؤقت إذا لم يكن موجوداً
os.makedirs(TEMP_DIR, exist_ok=True)

# إنشاء المجلدات الفرعية
os.makedirs(os.path.join(FONT_DIR, "previews"), exist_ok=True)
os.makedirs(os.path.join(FONT_DIR, "merged"), exist_ok=True)
os.makedirs(os.path.join(FONT_DIR, "logs"), exist_ok=True)

# ---------- Logging ----------
def get_unique_log_path():
    """الحصول على مسار فريد لملف السجل"""
    base_name = "merge_log"
    counter = 1
    log_file = os.path.join(FONT_DIR, "logs", f"{base_name}.txt")
    while os.path.exists(log_file):
        log_file = os.path.join(FONT_DIR, "logs", f"{base_name}_{counter}.txt")
        counter += 1
    return log_file

# باقي الكود كما هو. (لم يتغير اي منطق برمجي عدا المسارات) 
# ... (تابع باقي الكود الحالي من السطر 51 وما بعده)
