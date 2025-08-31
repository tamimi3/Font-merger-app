# main.py
import sys
import os
import traceback
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock

LOGFILE = os.path.join(os.path.expanduser("~"), "font_merger_app_log.txt")

def write_log(s):
    try:
        with open(LOGFILE, "a", encoding="utf-8") as f:
            f.write(s + "\n")
    except Exception:
        pass

# محاولة طلب الأذونات على أندرويد
def request_android_permissions(callback=None):
    try:
        # android.permissions يوفر Request runtime permission في p4a
        from android.permissions import request_permissions, Permission

        def _cb(permissions, grants):
            write_log(f"Permissions result: {permissions} -> {grants}")
            if callback:
                callback()
        request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE], _cb)
    except Exception as e:
        # إذا لم نكن على أندرويد أو المكتبة غير متاحة: نكمل بدون طلب
        write_log("No android.permissions available or running off-android: " + str(e))
        if callback:
            callback()

class Root(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.status = Label(text="جاهز")
        btn = Button(text="دمج الخطوط (Merge Fonts)", size_hint=(1, 0.2))
        btn.bind(on_release=lambda *_: Clock.schedule_once(lambda dt: self.start_merge(), 0))
        self.add_widget(self.status)
        self.add_widget(btn)

    def start_merge(self):
        self.status.text = "يبدأ الدمج..."
        write_log("Start merge pressed.")
        Clock.schedule_once(lambda dt: self._merge_worker(), 0)

    def _merge_worker(self):
        try:
            # مسار المجلد المتوقع على الجهاز
            target_dir = "/sdcard/fonts"
            if not os.path.isdir(target_dir):
                self.status.text = f"المجلد غير موجود: {target_dir}"
                write_log(f"Folder not found: {target_dir}")
                return

            # جمع ملفات ttf/otf
            fonts = [os.path.join(target_dir, f) for f in os.listdir(target_dir) if f.lower().endswith((".ttf", ".otf"))]
            write_log(f"Found fonts: {fonts}")
            if not fonts:
                self.status.text = "لم يتم العثور على خطوط في /sdcard/fonts"
                return

            # هنا تستدعي وظيفة الدمج الحقيقية — يمكنك تعديل هذه الجزئية
            out_path = os.path.join(target_dir, "merged_font.ttf")

            # محاولة استدعاء سكربت دمج خارجي (إن وُجد) وإلا سجل رسالة
            script_path = os.path.join(os.path.dirname(__file__), "merge_fonts.py")
            if os.path.exists(script_path):
                write_log(f"Calling local script: {script_path}")
                # استدعاء كعملية منفصلة لتقليل مخاطر انهيار الواجهة
                import subprocess
                cmd = [sys.executable, script_path, target_dir, out_path]
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                write_log("merge script stdout:\n" + proc.stdout)
                write_log("merge script stderr:\n" + proc.stderr)
                if proc.returncode == 0:
                    self.status.text = f"تم الدمج بنجاح: {out_path}"
                else:
                    self.status.text = "فشل الدمج (راجع السجل)"
                return
            else:
                # لا يوجد سكربت دمج: نضع رسالة واضحة للمستخدم
                self.status.text = "لا يوجد سكربت دمج مضمن. ضع ملف merge_fonts.py أو أضف منطق الدمج هنا."
                write_log("No merge_fonts.py found; skipping actual merge.")
                return

        except Exception as e:
            tb = traceback.format_exc()
            write_log("Exception in merge_worker:\n" + tb)
            self.status.text = "حدث خطأ — راجع السجل."

class FontMergerApp(App):
    def build(self):
        root = Root()
        # طلب الأذونات فور بدء التطبيق (Android)
        Clock.schedule_once(lambda dt: request_android_permissions(), 0.5)
        return root

    def on_start(self):
        write_log("App started. sys.argv: " + str(sys.argv))

if __name__ == '__main__':
    try:
        FontMergerApp().run()
    except Exception as e:
        tb = traceback.format_exc()
        write_log("Fatal exception on start:\n" + tb)
        raise
