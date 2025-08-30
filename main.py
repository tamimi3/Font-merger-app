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

FONT_DIR = "/sdcard/fonts"
TEMP_DIR = "/sdcard/fonts/temp_processing"
EN_PREVIEW = "The quick brown fox jumps over the lazy dog. 1234567890"
AR_PREVIEW = "سمَات مجّانِية، إختر منْ بين أكثر من ١٠٠ سمة مجانية او انشئ سماتك الخاصة هُنا في هذا التطبيق النظيف الرائع، وأظهر الابداع.١٢٣٤٥٦٧٨٩٠"

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

# ---------- Utilities ----------
def copy_to_temp(src_path, temp_dir):
    """نسخ الملف إلى المجلد المؤقت"""
    filename = os.path.basename(src_path)
    dst_path = os.path.join(temp_dir, filename)
    shutil.copy2(src_path, dst_path)
    return dst_path

def shutil_which(cmd):
    try:
        import shutil
        return shutil.which(cmd)
    except Exception:
        return None

def has_cff(path):
    try:
        f = TTFont(path)
        keys = f.keys()
        return ("CFF " in keys) or ("CFF2" in keys)
    except Exception:
        return False

# ---------- FontForge conversion ----------
def fontforge_convert_to_ttf(src, dst):
    s = src.replace('\\', '\\\\').replace('"', r'\"')
    d = dst.replace('\\', '\\\\').replace('"', r'\"')
    script = f'Open("{s}"); SelectWorthOutputting(); Generate("{d}"); Close();'
    cmd = ["fontforge", "-quiet", "-lang=ff", "-c", script]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
        if res.returncode == 0 and os.path.exists(dst):
            return True
        else:
            cmd2 = ["fontforge", "-quiet", "-lang=py", "-c", f'font=fontforge.open("{s}"); font.generate("{d}"); font.close()']
            res2 = subprocess.run(cmd2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
            if res2.returncode == 0 and os.path.exists(dst):
                return True
            return False
    except Exception as ex:
        return False

def convert_otf_to_ttf(path, temp_files):
    base, ext = os.path.splitext(path)
    try:
        font = TTFont(path)
    except Exception as ex:
        raise RuntimeError(f"Cannot open font {path}: {ex}")
    needs_conv = False
    if ext.lower() == ".otf":
        needs_conv = True
    if "CFF " in font.keys() or "CFF2" in font.keys():
        needs_conv = True
    if not needs_conv:
        return path
    out = base + "_to_ttf.ttf"
    if shutil_which("fontforge"):
        ok = fontforge_convert_to_ttf(path, out)
        if ok:
            temp_files.append(out)
            return out
    try:
        font.flavor = None
        font.save(out)
        temp_files.append(out)
        return out
    except Exception as ex:
        raise RuntimeError(f"Failed to convert {path} to TTF: {ex}")

# ---------- UnitsPerEm unification ----------
def try_unify_units(paths):
    fonts = []
    for p in paths:
        fonts.append(TTFont(p))
    units = [f['head'].unitsPerEm for f in fonts]
    target = max(units)
    for idx, f in enumerate(fonts):
        old = f['head'].unitsPerEm
        if old == target:
            continue
        scale = float(target) / float(old)
        try:
            if 'glyf' in f.keys():
                glyf = f['glyf']
                for gname in glyf.keys():
                    glyph = glyf[gname]
                    try:
                        if glyph.isComposite():
                            glyph.transform((scale, 0, 0, scale, 0, 0))
                            continue
                    except Exception:
                        pass
                    try:
                        coords, endPts, flags = glyph.getCoordinates(glyf)
                        for i in range(len(coords)):
                            x, y = coords[i]
                            coords[i] = (int(round(x * scale)), int(round(y * scale)))
                        try:
                            glyph.recalcBounds(glyf)
                        except Exception:
                            pass
                    except Exception:
                        pass
            try:
                hmtx = f['hmtx'].metrics
                for gname, (adv, lsb) in list(hmtx.items()):
                    hmtx[gname] = (int(round(adv * scale)), int(round(lsb * scale)))
            except Exception:
                pass
            if 'OS/2' in f.keys():
                try:
                    os2 = f['OS/2']
                    if hasattr(os2, 'usWinAscent'):
                        os2.usWinAscent = int(round(os2.usWinAscent * scale))
                        os2.usWinDescent = int(round(os2.usWinDescent * scale))
                except Exception:
                    pass
            if 'hhea' in f.keys():
                try:
                    f['hhea'].ascent = int(round(getattr(f['hhea'], 'ascent', 0) * scale))
                    f['hhea'].descent = int(round(getattr(f['hhea'], 'descent', 0) * scale))
                except Exception:
                    pass
            f['head'].unitsPerEm = int(target)
        except Exception as ex:
            try:
                hmtx = f['hmtx'].metrics
                for gname, (adv, lsb) in list(hmtx.items()):
                    hmtx[gname] = (int(round(adv * scale)), int(round(lsb * scale)))
                if 'OS/2' in f.keys():
                    os2 = f['OS/2']
                    if hasattr(os2, 'usWinAscent'):
                        os2.usWinAscent = int(round(os2.usWinAscent * scale))
                        os2.usWinDescent = int(round(os2.usWinDescent * scale))
                if 'hhea' in f.keys():
                    f['hhea'].ascent = int(round(getattr(f['hhea'], 'ascent', 0) * scale))
                    f['hhea'].descent = int(round(getattr(f['hhea'], 'descent', 0) * scale))
                f['head'].unitsPerEm = int(target)
            except Exception as ex2:
                pass
        try:
            f.save(paths[idx])
        except Exception as ex:
            pass
    return paths

# ---------- Subsetting ----------
def subset_keep(path, unicodes, temp_files):
    base, _ = os.path.splitext(path)
    out = base + "_sub.ttf"
    saved_argv = sys.argv[:]
    try:
        sys.argv = ["pyftsubset", path, f"--unicodes={unicodes}", f"--output-file={out}", "--no-hinting"]
        subset_main()
    except SystemExit:
        pass
    except Exception as ex:
        sys.argv = saved_argv
        return path
    finally:
        sys.argv = saved_argv
    if os.path.exists(out):
        temp_files.append(out)
        return out
    return path

def clean_languages(ar_path, en_path, temp_files):
    arabic_ranges = ",".join([
        "U+0600-06FF", "U+0750-077F", "U+08A0-08FF",
        "U+FB50-FDFF", "U+FE70-FEFF", "U+0660-0669"
    ])
    ascii_range = "U+0020-007F"
    ar_out = subset_keep(ar_path, arabic_ranges, temp_files)
    en_out = subset_keep(en_path, ascii_range, temp_files)
    return ar_out, en_out

# ---------- Unique output name ----------
def unique_name(path):
    base, ext = os.path.splitext(path)
    cand = path
    i = 1
    while os.path.exists(cand):
        cand = f"{base}_{i}{ext}"
        i += 1
    return cand

# ---------- Merge with FontForge ----------
def merge_fonts_with_fontforge(paths, out):
    try:
        script_content = f'''
Open("{paths[0]}")
MergeFonts("{paths[1]}")
Generate("{out}")
Close()
'''
        script_file = os.path.join(os.path.dirname(out), "_fontforge_merge.pe")
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(script_content)

        cmd = ["fontforge", "-script", script_file]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)

        if res.returncode == 0 and os.path.exists(out):
            try:
                os.remove(script_file)
            except:
                pass
            return out
        else:
            raise RuntimeError(f"FontForge merge failed: {res.stderr.strip()}")
    except Exception as ex:
        # Fallback to fontTools
        try:
            merger = Merger()
            merged = merger.merge(paths)
            merged.save(out)
            return out
        except Exception as ex2:
            raise RuntimeError(f"All merge methods failed: {ex}, {ex2}")

# ---------- Text shaping with Harfbuzz ----------
def shape_text_harfbuzz(text, font_path, font_size, direction='ltr'):
    if hb is None:
        return None

    try:
        with open(font_path, 'rb') as font_file:
            font_data = font_file.read()

        face = hb.Face(font_data)
        font = hb.Font(face)
        font.scale = (font_size, font_size)
        hb.ot_font_set_funcs(font)

        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()

        if direction == 'rtl':
            buf.direction = 'rtl'
            buf.script = 'arab'
            buf.language = 'ar'

        hb.shape(font, buf)

        infos = buf.glyph_infos
        positions = buf.glyph_positions

        width = sum(pos.x_advance for pos in positions) / 64
        height = font_size

        return width, height, infos, positions, font

    except Exception as e:
        return None

# ---------- Text wrapping helper ----------
def wrap_text_to_lines(text, font, max_width, is_ar=False, draw=None):
    if draw is None:
        draw = ImageDraw.Draw(Image.new("RGB", (10,10)))
    words = text.split(" ")
    lines = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip() if cur else w
        if is_ar:
            bbox = draw.textbbox((0,0), trial, font=font, direction="rtl", language="ar")
        else:
            bbox = draw.textbbox((0,0), trial, font=font)
        w_px = bbox[2] - bbox[0]
        if w_px <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            if is_ar:
                single_bbox = draw.textbbox((0,0), w, font=font, direction="rtl", language="ar")
            else:
                single_bbox = draw.textbbox((0,0), w, font=font)
            if single_bbox[2] - single_bbox[0] > max_width:
                part = ""
                for ch in w:
                    trial2 = part + ch
                    if is_ar:
                        bbox2 = draw.textbbox((0,0), trial2, font=font, direction="rtl", language="ar")
                    else:
                        bbox2 = draw.textbbox((0,0), trial2, font=font)
                    if bbox2[2] - bbox2[0] <= max_width:
                        part = trial2
                    else:
                        if part:
                            lines.append(part)
                        part = ch
                if part:
                    cur = part
                else:
                    cur = ""
            else:
                cur = w
    if cur:
        lines.append(cur)
    return lines

# ---------- Preview creation (high resolution) ----------
def create_preview(merged_ttf, out_jpg, bg_color="white", text_color="black"):
    W, H = 6400, 2880  # دقة عالية
    img = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(img)

    try:
        has_raqm = features.check_module("raqm")

        base_size = 330

        try:
            font_en = ImageFont.truetype(merged_ttf, base_size)
            font_ar = ImageFont.truetype(merged_ttf, base_size)
        except Exception:
            font_en = ImageFont.load_default()
            font_ar = ImageFont.load_default()

        max_w = int(W * 0.9)

        size = base_size
        while True:
            try:
                font_en = ImageFont.truetype(merged_ttf, size)
            except Exception:
                font_en = ImageFont.load_default()
            bbox = draw.textbbox((0,0), EN_PREVIEW, font=font_en)
            w = bbox[2] - bbox[0]
            if w >= W * 0.85 or size >= 1500:
                break
            size += 75

        size = int(size * 0.9)

        try:
            font_en = ImageFont.truetype(merged_ttf, size)
            font_ar = ImageFont.truetype(merged_ttf, size)
        except Exception:
            font_en = ImageFont.load_default()
            font_ar = ImageFont.load_default()

        en_lines = wrap_text_to_lines(EN_PREVIEW, font_en, max_w, is_ar=False, draw=draw)

        if has_raqm:
            ar_text = AR_PREVIEW
            use_rtl = True
        else:
            reshaped_ar = arabic_reshaper.reshape(AR_PREVIEW)
            ar_text = get_display(reshaped_ar)
            use_rtl = False

        ar_lines = wrap_text_to_lines(ar_text, font_ar, max_w, is_ar=use_rtl, draw=draw)

        spacing = int(size * 0.2)
        ar_total_h = 0
        for ln in ar_lines:
            if use_rtl:
                bbox = draw.textbbox((0,0), ln, font=font_ar, direction="rtl", language="ar")
            else:
                bbox = draw.textbbox((0,0), ln, font=font_ar)
            ar_total_h += (bbox[3] - bbox[1]) + spacing
        ar_total_h -= spacing

        en_total_h = 0
        for ln in en_lines:
            bbox = draw.textbbox((0,0), ln, font=font_en)
            en_total_h += (bbox[3] - bbox[1]) + spacing
        en_total_h -= spacing

        start_en_y = max(20, (H//2 - en_total_h) // 2)
        y = start_en_y
        for ln in en_lines:
            bbox = draw.textbbox((0,0), ln, font=font_en)
            w = bbox[2] - bbox[0]
            x = (W - w) / 2
            draw.text((x, y), ln, font=font_en, fill=text_color)
            y += (bbox[3] - bbox[1]) + spacing

        start_ar_y = H//2 + max(20, (H//2 - ar_total_h) // 2)
        start_ar_y -= 100
        y = start_ar_y
        for ln in ar_lines:
            if use_rtl:
                bbox = draw.textbbox((0,0), ln, font=font_ar, direction="rtl", language="ar")
                w = bbox[2] - bbox[0]
                x = (W - w) / 2
                draw.text((x, y), ln, font=font_ar, fill=text_color, direction="rtl", language="ar")
            else:
                bbox = draw.textbbox((0,0), ln, font=font_ar)
                w = bbox[2] - bbox[0]
                x = (W - w) / 2
                draw.text((x, y), ln, font=font_ar, fill=text_color)
            y += (bbox[3] - bbox[1]) + spacing

        img.save(out_jpg, "JPEG", quality=95, dpi=(600, 600))
        return True
    except Exception as ex:
        try:
            f_default = ImageFont.load_default()
            draw.text((100, 500), EN_PREVIEW, font=f_default, fill=text_color)

            try:
                draw.text((100, H//2 + 500), AR_PREVIEW, font=f_default, fill=text_color, direction="rtl", language="ar")
            except:
                reshaped_ar = arabic_reshaper.reshape(AR_PREVIEW)
                bidi_ar = get_display(reshaped_ar)
                draw.text((100, H//2 + 500), bidi_ar, font=f_default, fill=text_color)

            img.save(out_jpg, "JPEG", quality=95)
            return False
        except Exception as ex2:
            return False

# ---------- الدالة الرئيسية المعدلة ----------
def merge_fonts(a_name, e_name):
    logs = []
    LOG_FILE = get_unique_log_path()
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        ts = time.strftime("%Y-%m-%d %I:%M:%S %p")
        f.write(f"{ts} - بدء دمج الخطوط\n")

    def add_log(msg):
        logs.append(msg)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{msg}\n")

    add_log("=== بدء دمج الخطوط ===")

    if not os.path.isdir(FONT_DIR):
        add_log(f"مجلد الخطوط غير موجود: {FONT_DIR}")
        return '\n'.join(logs) + "\n✗ Failed"

    a_path = os.path.join(FONT_DIR, a_name)
    e_path = os.path.join(FONT_DIR, e_name)

    if not os.path.exists(a_path):
        add_log(f"الخط العربي غير موجود: {a_path}")
        return '\n'.join(logs) + "\n✗ Failed"
    if not os.path.exists(e_path):
        add_log(f"الخط الإنجليزي غير موجود: {e_path}")
        return '\n'.join(logs) + "\n✗ Failed"

    processing_dir = tempfile.mkdtemp(dir=TEMP_DIR)

    try:
        a_temp = copy_to_temp(a_path, processing_dir)
        e_temp = copy_to_temp(e_path, processing_dir)

        temp_files = []

        # الخطوات بدون progress bar
        a_ttf = convert_otf_to_ttf(a_temp, temp_files)
        add_log("تم تحويل الخط العربي إلى TTF")

        e_ttf = convert_otf_to_ttf(e_temp, temp_files)
        add_log("تم تحويل الخط الإنجليزي إلى TTF")

        a_ttf, e_ttf = try_unify_units([a_ttf, e_ttf])
        add_log("تم توحيد unitsPerEm")

        a_clean, e_clean = clean_languages(a_ttf, e_ttf, temp_files)
        add_log("تم تنظيف اللغات")

        outname = os.path.splitext(os.path.basename(a_name))[0] + "_" + os.path.splitext(os.path.basename(e_name))[0] + ".ttf"
        outpath = unique_name(os.path.join(processing_dir, outname))
        merged_path = merge_fonts_with_fontforge([a_clean, e_clean], outpath)
        add_log("تم الدمج")

        preview_name = os.path.splitext(os.path.basename(merged_path))[0] + ".jpg"
        preview_path = unique_name(os.path.join(processing_dir, preview_name))
        create_preview(merged_path, preview_path)
        add_log("تم إنشاء المعاينة")

        preview_121212_name = os.path.splitext(os.path.basename(merged_path))[0] + "_121212.jpg"
        preview_121212_path = unique_name(os.path.join(processing_dir, preview_121212_name))
        create_preview(merged_path, preview_121212_path, bg_color=(18,18,18), text_color="white")
        add_log("تم إنشاء المعاينة الداكنة")

        final_font_path = unique_name(os.path.join(FONT_DIR, "merged", os.path.basename(merged_path)))
        shutil.move(merged_path, final_font_path)

        final_preview_path = unique_name(os.path.join(FONT_DIR, "previews", os.path.basename(preview_path)))
        shutil.move(preview_path, final_preview_path)

        final_preview_121212_path = unique_name(os.path.join(FONT_DIR, "previews", os.path.basename(preview_121212_path)))
        shutil.move(preview_121212_path, final_preview_121212_path)

        result = "✓ Successful\n" + final_font_path + "\n" + final_preview_path + "\n" + final_preview_121212_path
        add_log(result)
        return '\n'.join(logs) + "\n" + result

    except Exception as main_ex:
        add_log(str(main_ex))
        return '\n'.join(logs) + "\n✗ Failed"
    finally:
        shutil.rmtree(processing_dir, ignore_errors=True)

# ---------- Kivy App ----------
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView

class MergeApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.ar_input = TextInput(hint_text='اسم الخط العربي (مثال: arabic.ttf)', multiline=False)
        self.en_input = TextInput(hint_text='اسم الخط الإنجليزي (مثال: english.ttf)', multiline=False)

        btn = Button(text='دمج الخطوط', size_hint=(1, 0.2))
        btn.bind(on_press=self.do_merge)

        self.output_scroll = ScrollView()
        self.output = Label(text='', size_hint_y=None, height=300, text_size=(None, None))
        self.output.bind(texture_size=self.output.setter('size'))
        self.output_scroll.add_widget(self.output)

        layout.add_widget(self.ar_input)
        layout.add_widget(self.en_input)
        layout.add_widget(btn)
        layout.add_widget(self.output_scroll)

        return layout

    def do_merge(self, instance):
        a = self.ar_input.text.strip()
        e = self.en_input.text.strip()
        if not a or not e:
            self.output.text = 'يرجى إدخال أسماء الخطوط'
            return
        result = merge_fonts(a, e)
        self.output.text = result

if __name__ == "__main__":
    MergeApp().run()
