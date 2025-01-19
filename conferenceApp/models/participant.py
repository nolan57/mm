from django.db import models
from django.conf import settings
from .company import Company
from .contact import ContactPerson

User = settings.AUTH_USER_MODEL

class ParticipantInfoChange(models.Model):
    """参会人信息变更记录"""
    participant = models.ForeignKey('Participant', on_delete=models.CASCADE, 
                                  related_name='info_changes', verbose_name='参会人')
    field_name = models.CharField(max_length=100, verbose_name='变更字段')
    old_value = models.TextField(verbose_name='原值')
    new_value = models.TextField(verbose_name='新值')
    status = models.CharField(max_length=20, choices=(
        ('pending', '待审核'),
        ('approved', '已通过'),
        ('rejected', '已拒绝'),
    ), default='pending', verbose_name='审核状态')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                 related_name='submitted_changes', verbose_name='提交人')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                  related_name='reviewed_changes', verbose_name='审核人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    review_comment = models.TextField(blank=True, verbose_name='审核意见')

    class Meta:
        verbose_name = '信息变更记录'
        verbose_name_plural = '信息变更记录'
        ordering = ['-created_at']

class Participant(models.Model):
    STATUS_CHOICES = (
        ('pending', '待确认'),
        ('confirmed', '已确认'),
        ('checked_in', '已签到'),
        ('cancelled', '已取消'),
    )

    company = models.ForeignKey(Company, on_delete=models.CASCADE, 
                              related_name='participants', verbose_name='所属公司')
    registered_by = models.ForeignKey(ContactPerson, on_delete=models.CASCADE,
                                    related_name='registered_participants', verbose_name='登记人')
    contact_person = models.ForeignKey(ContactPerson, on_delete=models.SET_NULL, 
                                     null=True, blank=True,
                                     related_name='as_participant', verbose_name='关联联系人')
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True,
                              related_name='participant_profile', verbose_name='关联用户')
    name = models.CharField(max_length=100, verbose_name='姓名')
    position = models.CharField(max_length=100, verbose_name='职位')
    phone = models.CharField(max_length=20, verbose_name='联系电话')
    email = models.EmailField(verbose_name='邮箱')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, 
                            default='pending', verbose_name='状态')
    registration_number = models.CharField(max_length=50, unique=True, 
                                        verbose_name='登记编号')
    check_in_time = models.DateTimeField(null=True, blank=True, 
                                       verbose_name='签到时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    info_verified = models.BooleanField(default=False, verbose_name='信息已验证')
    verification_code = models.CharField(max_length=6, blank=True, verbose_name='验证码')
    verification_code_expires = models.DateTimeField(null=True, blank=True, 
                                                   verbose_name='验证码过期时间')

    class Meta:
        verbose_name = '参会人员'
        verbose_name_plural = '参会人员'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['registration_number']),
            models.Index(fields=['status']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.name} - {self.company.name}"

    def save(self, *args, **kwargs):
        # 如果是新创建的参会人员，生成登记编号
        if not self.registration_number:
            self.registration_number = self._generate_registration_number()
        
        # 如果关联了联系人，自动同步联系人信息
        if self.contact_person and not kwargs.pop('skip_contact_sync', False):
            self.name = self.contact_person.user.name
            self.position = self.contact_person.position
            self.phone = self.contact_person.phone
            self.email = self.contact_person.email
            self.user = self.contact_person.user
            self.info_verified = True  # 联系人信息默认已验证
            
        super().save(*args, **kwargs)

    def _generate_registration_number(self):
        """生成登记编号：公司编码 + 年月日 + 4位序号"""
        from django.utils import timezone
        import random
        
        date_str = timezone.now().strftime('%Y%m%d')
        company_code = self.company.code
        
        # 生成4位随机序号
        while True:
            sequence = str(random.randint(1, 9999)).zfill(4)
            registration_number = f"{company_code}{date_str}{sequence}"
            
            # 检查是否已存在
            if not Participant.objects.filter(registration_number=registration_number).exists():
                return registration_number

    def create_user_account(self):
        """创建关联的用户账号"""
        if not self.user and self.email:
            from django.contrib.auth.models import Group
            from django.utils.crypto import get_random_string
            
            # 如果已经存在同邮箱的用户，直接关联
            existing_user = User.objects.filter(email=self.email).first()
            if existing_user:
                self.user = existing_user
                self.save(skip_contact_sync=True)
                return None
            
            # 创建新用户
            temp_password = get_random_string(12)
            user = User.objects.create_user(
                username=self.email,
                email=self.email,
                password=temp_password,
                first_name=self.name,
            )
            
            # 添加到参会人用户组
            participant_group, _ = Group.objects.get_or_create(name='Participants')
            user.groups.add(participant_group)
            
            # 关联用户
            self.user = user
            self.save(skip_contact_sync=True)
            
            # 返回临时密码
            return temp_password
        return None

    def request_info_change(self, field_name, new_value, user):
        """申请信息变更"""
        # 如果是关联的联系人，不允许直接修改信息
        if self.contact_person:
            raise ValidationError('您的信息与公司联系人关联，请联系管理员修改')
            
        old_value = getattr(self, field_name)
        return ParticipantInfoChange.objects.create(
            participant=self,
            field_name=field_name,
            old_value=str(old_value),
            new_value=str(new_value),
            created_by=user
        )

    def generate_verification_code(self):
        """生成验证码"""
        # 如果是关联的联系人，不需要验证
        if self.contact_person:
            return None
            
        import random
        from django.utils import timezone
        
        # 生成6位数字验证码
        self.verification_code = str(random.randint(100000, 999999))
        # 设置过期时间为30分钟后
        self.verification_code_expires = timezone.now() + timezone.timedelta(minutes=30)
        self.save(skip_contact_sync=True)
        return self.verification_code

    def verify_code(self, code):
        """验证验证码"""
        # 如果是关联的联系人，不需要验证
        if self.contact_person:
            return True
            
        from django.utils import timezone
        
        if (self.verification_code and 
            self.verification_code == code and 
            self.verification_code_expires and 
            self.verification_code_expires > timezone.now()):
            self.info_verified = True
            self.verification_code = ''
            self.verification_code_expires = None
            self.save(skip_contact_sync=True)
            return True
        return False

    def check_in(self):
        """签到"""
        from django.utils import timezone
        if self.status == 'confirmed':
            self.status = 'checked_in'
            self.check_in_time = timezone.now()
            self.save()
            return True
        return False
