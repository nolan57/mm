from django.db import models
from django.conf import settings
from .conference import Conference
from .company import Company

class Contact(models.Model):
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=100, verbose_name='姓名')
    title = models.CharField(max_length=100, verbose_name='职位', blank=True)
    phone = models.CharField(max_length=20, verbose_name='电话')
    email = models.EmailField(verbose_name='邮箱')
    description = models.TextField(verbose_name='描述', blank=True, help_text='联系人的其他信息，如负责的具体事项等')
    is_primary = models.BooleanField(default=False, verbose_name='主要联系人')
    
    class Meta:
        verbose_name = '联系人'
        verbose_name_plural = '联系人列表'
        ordering = ['-is_primary', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.title})"

class ContactTag(models.Model):
    """联系人标签"""
    name = models.CharField(max_length=50, unique=True, verbose_name='标签名称')
    description = models.TextField(blank=True, verbose_name='描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '联系人标签'
        verbose_name_plural = '联系人标签列表'
        ordering = ['name']

    def __str__(self):
        return self.name

class ContactPerson(models.Model):
    """联系人模型，用于管理公司的联系人"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='contact_roles',
        verbose_name='用户'
    )
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='contacts', verbose_name='所属公司')
    position = models.CharField(max_length=100, verbose_name='职位', blank=True)
    phone = models.CharField(max_length=20, verbose_name='电话')
    email = models.EmailField(verbose_name='邮箱')
    is_primary = models.BooleanField(default=False, verbose_name='主要联系人')
    tags = models.ManyToManyField(ContactTag, related_name='contacts', blank=True, verbose_name='标签')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '公司联系人'
        verbose_name_plural = '公司联系人列表'
        ordering = ['-is_primary', 'user__email']  # 使用 email 作为排序字段，因为它一定存在
        unique_together = [['user', 'company']]  # 同一个用户在同一个公司中只能有一个联系人记录

    def __str__(self):
        name = self.user.get_full_name() if self.user else '未知用户'
        return f"{name} ({self.position})" if self.position else name

    def save(self, *args, **kwargs):
        # 如果设置为主要联系人，则将同一公司的其他联系人设置为非主要联系人
        if self.is_primary:
            ContactPerson.objects.filter(company=self.company).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

class ConferenceContact(models.Model):
    """会议联系人模型，用于管理联系人在特定会议中的角色"""
    ROLE_CHOICES = [
        ('organizer', '主办方'),
        ('speaker', '演讲者'),
        ('participant', '参会者'),
        ('staff', '工作人员'),
    ]

    contact = models.ForeignKey(ContactPerson, on_delete=models.CASCADE, related_name='conference_roles', verbose_name='联系人')
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name='contact_roles', verbose_name='会议')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name='角色')
    is_primary = models.BooleanField(default=False, verbose_name='主要联系人')
    notes = models.TextField(blank=True, verbose_name='备注', help_text='联系人在此会议中的具体职责或其他信息')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '会议联系人'
        verbose_name_plural = '会议联系人列表'
        ordering = ['-is_primary', 'role', 'contact__user__name']
        unique_together = [['contact', 'conference', 'role']]  # 同一个联系人在同一个会议中的同一角色只能有一条记录

    def __str__(self):
        return f"{self.contact.user.name} - {self.get_role_display()} at {self.conference.name}"

    def save(self, *args, **kwargs):
        # 如果设置为主要联系人，则将同一会议同一角色的其他联系人设置为非主要联系人
        if self.is_primary:
            ConferenceContact.objects.filter(
                conference=self.conference,
                role=self.role
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)
