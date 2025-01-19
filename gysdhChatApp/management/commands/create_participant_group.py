from django.core.management.base import BaseCommand
from gysdhChatApp.models import UserGroup

class Command(BaseCommand):
    help = '创建参会人用户组'

    def handle(self, *args, **options):
        # 检查参会人用户组是否已存在
        group_name = '参会人'
        if UserGroup.objects.filter(name=group_name).exists():
            self.stdout.write(self.style.WARNING(f'用户组 "{group_name}" 已存在'))
            return

        # 创建参会人用户组
        group = UserGroup.objects.create(
            name=group_name,
            description='会议参会人员用户组'
        )

        self.stdout.write(self.style.SUCCESS(f'成功创建用户组 "{group_name}"'))
