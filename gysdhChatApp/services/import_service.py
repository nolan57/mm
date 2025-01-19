import pandas as pd
from django.db import transaction
from django.core.exceptions import ValidationError
from ..models import User, Company
from ..services.email_service import send_user_credentials_email

class UserImportService:
    REQUIRED_COLUMNS = ['姓名', '邮箱', '公司代码']
    
    def __init__(self):
        self.errors = []
        self.success_count = 0
        self.error_count = 0
        self.processed_users = []

    def validate_file(self, file):
        """验证Excel文件格式和必要列"""
        try:
            df = pd.read_excel(file)
            missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
            if missing_columns:
                self.errors.append(f"缺少必要列：{', '.join(missing_columns)}")
                return False
            return df
        except Exception as e:
            self.errors.append(f"文件读取错误：{str(e)}")
            return False

    def process_row(self, row):
        """处理单行数据"""
        try:
            # 查找公司
            company = Company.objects.filter(code=row['公司代码']).first()
            if not company:
                raise ValidationError(f"找不到公司代码为 {row['公司代码']} 的公司")

            # 创建用户
            user = User(
                name=row['姓名'],
                email=row['邮箱'],
                company=company
            )
            
            # 生成随机密码
            password = User.objects.make_random_password()
            user.original_password = password
            user.set_password(password)
            
            # 保存用户
            user.save()
            
            # 发送邮件通知
            send_user_credentials_email(user, password, is_new=True)
            
            self.success_count += 1
            self.processed_users.append({
                'user': user,
                'status': 'success',
                'message': '导入成功'
            })
            
        except Exception as e:
            self.error_count += 1
            self.processed_users.append({
                'row': row,
                'status': 'error',
                'message': str(e)
            })

    @transaction.atomic
    def import_users(self, file):
        """导入用户数据"""
        df = self.validate_file(file)
        if not df:
            return False

        # 处理每一行数据
        for index, row in df.iterrows():
            self.process_row(row)

        return {
            'success_count': self.success_count,
            'error_count': self.error_count,
            'errors': self.errors,
            'processed_users': self.processed_users
        }
