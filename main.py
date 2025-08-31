from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from android.permissions import request_permissions, Permission
import os
from fonttools.merge import Merger  # تأكد من تثبيت fonttools في requirements

class FontMergerApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical')
        self.status = Label(text='جاهز للدمج...')
        button = Button(text='دمج الخطوط')
        button.bind(on_press=self.merge_fonts)
        layout.add_widget(self.status)
        layout.add_widget(button)
        request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])  # طلب الإذونات
        return layout

    def merge_fonts(self, instance):
        try:
            fonts_dir = '/sdcard/fonts'
            if not os.path.exists(fonts_dir):
                os.makedirs(fonts_dir)
                self.status.text = 'تم إنشاء المجلد /sdcard/fonts'
                return

            font_files = [f for f in os.listdir(fonts_dir) if f.endswith(('.ttf', '.otf'))]
            if len(font_files) < 2:
                self.status.text = 'ضع خطوطاً أكثر في /sdcard/fonts'
                return

            merger = Merger()
            merged = merger.merge([os.path.join(fonts_dir, f) for f in font_files])
            output_path = os.path.join(fonts_dir, 'merged_font.ttf')
            merged.font.save(output_path)
            self.status.text = f'تم الدمج في {output_path}'

        except Exception as e:
            self.status.text = f'خطأ: {str(e)}'
            print(e)  # للسجلات في logcat

if __name__ == '__main__':
    FontMergerApp().run()
