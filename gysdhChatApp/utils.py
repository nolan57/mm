from django.core.mail import send_mail
from django.conf import settings
from .models import User, Company
import pandas as pd
from django.db import transaction
from django.contrib.auth.hashers import make_password
from .services.email_service import send_user_credentials_email

def send_announcement_email(announcement):
    """
    发送公告邮件给所有不在线的用户
    """
    # 获取所有不在线且有邮箱的用户
    offline_users = User.objects.filter(is_online=False, email__isnull=False)
    
    if not offline_users.exists():
        return
    
    subject = '新公告通知'
    message = f'''
您好！

有新的公告发布：

{announcement.content}

此邮件由系统自动发送，请勿回复。
'''
    
    recipient_list = [user.email for user in offline_users]
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=False,
        )
    except Exception as e:
        print(f"发送邮件失败: {str(e)}")  # 在实际生产环境中应该使用proper logging

def import_users_from_excel(file_path):
    """
    从Excel文件批量导入用户
    Excel文件应包含以下列：
    - name (姓名)
    - company_code (公司代码)
    - email (邮箱)
    - is_admin (是否管理员，可选)
    - can_publish_announcements (是否可以发布公告，可选)
    - can_private_message (是否可以发私信，可选)
    - is_event_staff (是否是活动工作人员，可选)
    """
    try:
        # 读取Excel文件
        df = pd.read_excel(file_path)
        
        # 验证必需的列是否存在
        required_columns = ['name', 'company_code', 'email']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f'Excel文件缺少必需的列：{col}')
        
        # 验证所有公司代码是否存在
        company_codes = df['company_code'].unique()
        existing_companies = Company.objects.filter(code__in=company_codes)
        existing_codes = {company.code for company in existing_companies}
        missing_codes = set(company_codes) - existing_codes
        if missing_codes:
            raise ValueError(f'以下公司代码不存在：{", ".join(missing_codes)}')

        # 验证邮箱格式
        import re
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        
        # 准备结果统计
        results = {
            'success': 0,
            'failed': 0,
            'errors': [],
            'created_users': [],  # 记录创建的用户信息
            'email_failed': []    # 记录邮件发送失败的用户
        }
        
        # 开始批量导入
        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    # 验证邮箱格式
                    if not email_pattern.match(str(row['email']).strip()):
                        results['failed'] += 1
                        results['errors'].append(f"第 {index+2} 行的邮箱格式不正确")
                        continue
                        
                    # 检查邮箱是否已存在
                    if User.objects.filter(email=row['email']).exists():
                        results['failed'] += 1
                        results['errors'].append(f"邮箱 {row['email']} 已被使用")
                        continue
                    
                    # 获取对应的公司
                    try:
                        company = Company.objects.get(code=row['company_code'])
                    except Company.DoesNotExist:
                        results['failed'] += 1
                        results['errors'].append(f"第 {index+2} 行的公司代码 {row['company_code']} 不存在")
                        continue
                    
                    # 准备用户数据
                    user_data = {
                        'name': row['name'],
                        'company': company,
                        'email': str(row['email']).strip(),
                        'is_admin': row.get('is_admin', False),
                        'can_publish_announcements': row.get('can_publish_announcements', False),
                        'can_private_message': row.get('can_private_message', False),
                        'is_event_staff': row.get('is_event_staff', False),
                    }
                    
                    # 创建用户（密码将自动生成）
                    user = User.objects.create_user(**user_data)
                    results['success'] += 1
                    
                    # 发送邮件通知
                    if not send_user_credentials_email(user, user.original_password, is_new=True):
                        results['email_failed'].append({
                            'number': user.number,
                            'name': user.name,
                            'email': user.email,
                            'password': user.original_password
                        })
                    
                    # 记录创建的用户信息（仅当邮件发送失败时需要）
                    if user.number in [u['number'] for u in results['email_failed']]:
                        results['created_users'].append({
                            'number': user.number,
                            'name': user.name,
                            'email': user.email,
                            'password': user.original_password
                        })
                    
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"导入第 {index+2} 行失败: {str(e)}")
        
        return results
        
    except Exception as e:
        return {
            'success': 0,
            'failed': 0,
            'errors': [f'文件处理失败: {str(e)}'],
            'created_users': [],
            'email_failed': []
        }

def update_email_settings():
    """
    从 SystemSettings 更新邮件配置
    """
    from django.conf import settings
    from .models import SystemSettings

    system_settings = SystemSettings.get_settings()
    
    # 更新Django邮件设置
    if system_settings.email_host:
        settings.EMAIL_HOST = system_settings.email_host
    if system_settings.email_port:
        settings.EMAIL_PORT = system_settings.email_port
    if system_settings.email_host_user:
        settings.EMAIL_HOST_USER = system_settings.email_host_user
        settings.DEFAULT_FROM_EMAIL = system_settings.email_host_user
    if system_settings.email_host_password:
        settings.EMAIL_HOST_PASSWORD = system_settings.email_host_password
    
    settings.EMAIL_USE_TLS = system_settings.email_use_tls
    settings.EMAIL_USE_SSL = not system_settings.email_use_tls  # 如果不使用TLS，则使用SSL

def send_test_email(to_email):
    """
    发送测试邮件以验证邮件配置
    """
    try:
        send_mail(
            subject='测试邮件',
            message='这是一封测试邮件，用于验证邮件配置是否正确。',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=False,
        )
        return True, "测试邮件发送成功"
    except Exception as e:
        return False, f"发送邮件失败: {str(e)}"
