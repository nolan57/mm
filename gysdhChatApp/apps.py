from django.apps import AppConfig

class GysdhchatappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gysdhChatApp'
    verbose_name = '聊天系统'

    def ready(self):
        # 导入信号处理器
        from . import signals
        # 更新邮件配置
        from .utils import update_email_settings
        update_email_settings()
