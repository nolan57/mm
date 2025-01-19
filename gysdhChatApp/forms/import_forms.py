from django import forms

class UserImportForm(forms.Form):
    file = forms.FileField(
        label='Excel文件',
        help_text='请上传包含用户信息的Excel文件(.xlsx)',
        widget=forms.FileInput(attrs={'accept': '.xlsx'})
    )
