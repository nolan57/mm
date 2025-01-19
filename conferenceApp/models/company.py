from django.db import models

class Company(models.Model):
    name = models.CharField(max_length=200, verbose_name='公司名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='公司编码')
    business_type = models.CharField(max_length=100, verbose_name='业务类型')
    address = models.CharField(max_length=500, blank=True, verbose_name='公司地址')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '公司'
        verbose_name_plural = '公司'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.code})"
