from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import SystemSettings
from .utils import update_email_settings

@receiver(post_save, sender=SystemSettings)
def update_email_settings_on_save(sender, instance, **kwargs):
    """
    当 SystemSettings 保存时更新邮件配置
    """
    update_email_settings()
