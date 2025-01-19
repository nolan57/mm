from django.db import models
from ckeditor.fields import RichTextField

# Create your models here.

class Conference(models.Model):
    name = models.CharField(max_length=255)
    registration_start = models.DateTimeField()
    registration_end = models.DateTimeField()
    # ... other existing fields ...

class RegistrationForm(models.Model):
    title = models.CharField(max_length=255)
    description = RichTextField(blank=True)
    max_participants = models.PositiveIntegerField(default=1)
    conference = models.ForeignKey('Conference', related_name='registration_forms', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class FormField(models.Model):
    FIELD_TYPES = [
        ('text', '文本'),
        ('textarea', '多行文本'),
        ('select', '下拉选择'),
        ('radio', '单选'),
        ('checkbox', '多选'),
        ('date', '日期'),
    ]
    
    form = models.ForeignKey(RegistrationForm, related_name='fields', on_delete=models.CASCADE)
    label = models.CharField(max_length=255)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    required = models.BooleanField(default=False)
    help_text = models.CharField(max_length=255, blank=True)
    placeholder = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)
    options = models.TextField(blank=True, help_text='For select/radio/checkbox fields, separate options with commas')
    
    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.form.title} - {self.label}"

class FormResponse(models.Model):
    form = models.ForeignKey(RegistrationForm, related_name='responses', on_delete=models.CASCADE)
    participant = models.ForeignKey('Participant', related_name='form_responses', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class FormFieldResponse(models.Model):
    response = models.ForeignKey(FormResponse, related_name='field_responses', on_delete=models.CASCADE)
    field = models.ForeignKey(FormField, related_name='responses', on_delete=models.CASCADE)
    value = models.TextField()

    def __str__(self):
        return f"{self.field.label}: {self.value}"
