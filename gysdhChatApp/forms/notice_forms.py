from django import forms
from ..models import Notice, Announcement
from django_summernote.widgets import SummernoteWidget

class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = ['content']
        widgets = {
            'content': SummernoteWidget(attrs={
                'summernote': {
                    'width': '100%',
                    'height': '300px',
                    'toolbar': [
                        ['style', ['style']],
                        ['font', ['bold', 'underline', 'clear']],
                        ['color', ['color']],
                        ['para', ['ul', 'ol', 'paragraph']],
                        ['table', ['table']],
                        ['insert', ['link', 'picture']],
                        ['view', ['fullscreen', 'codeview']]
                    ],
                    'lang': 'zh-CN'
                }
            })
        }

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['content', 'priority', 'expires_at', 'is_sticky', 'file']
        widgets = {
            'content': SummernoteWidget(attrs={
                'summernote': {
                    'width': '100%',
                    'height': '300px',
                    'toolbar': [
                        ['style', ['style']],
                        ['font', ['bold', 'underline', 'clear']],
                        ['color', ['color']],
                        ['para', ['ul', 'ol', 'paragraph']],
                        ['table', ['table']],
                        ['insert', ['link', 'picture']],
                        ['view', ['fullscreen', 'codeview']]
                    ],
                    'lang': 'zh-CN'
                }
            }),
            'expires_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'is_sticky': forms.CheckboxInput(attrs={
                'class': 'custom-checkbox',
                'style': 'border-radius: 9999px;'
            }),
        }
