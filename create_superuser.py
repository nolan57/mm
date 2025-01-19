import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gysdhChatProject.settings')
django.setup()

from gysdhChatApp.models import User
from conferenceApp.models import Company

def create_superuser():
    try:
        # 创建或获取系统管理员公司
        company, created = Company.objects.get_or_create(
            code='000000',
            defaults={
                'name': '系统管理员公司',
                'business_type': '系统管理'
            }
        )
        
        # 检查是否已存在超级用户
        if User.objects.filter(is_admin=True).exists():
            print('超级用户已存在')
            return
        
        # 创建超级用户
        superuser = User.objects.create_superuser(
            name='超级管理员',
            company=company,
            email='admin@example.com',
            password='admin123456'
        )
        
        print(f'超级用户创建成功')
        print(f'用户编号: {superuser.number}')
        print('邮箱: admin@example.com')
        print('密码: admin123456')
        print('请登录后立即修改密码')
        
    except Exception as e:
        print(f'创建超级用户失败: {str(e)}')

if __name__ == '__main__':
    create_superuser()
