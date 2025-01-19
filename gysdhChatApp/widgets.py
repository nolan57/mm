from django import forms

class QuillWidget(forms.Textarea):
    template_name = 'widgets/quill.html'
    
    class Media:
        css = {
            'all': (
                'https://cdn.quilljs.com/1.3.7/quill.snow.css',
            )
        }
        js = (
            'https://cdn.quilljs.com/1.3.7/quill.min.js',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs['class'] = 'quill-editor'
        # 设置编辑器配置
        self.attrs.update({
            'data-toolbar-config': '[["header", "bold", "italic", "underline", {"list": "ordered"}, {"list": "bullet"}, {"align": []}], ["blockquote", "code-block", {"color": []}, {"background": []}, "link", "image"]]'
        })
