from django.db import models
from django.core.exceptions import ValidationError
from .contact import ContactPerson
from .participant import Participant
from .conference import Conference  # Import Conference model

class RegistrationForm(models.Model):
    """报名表单定义"""
    title = models.CharField(max_length=100, verbose_name='表单标题', default='未命名表单')
    description = models.TextField(null=True, blank=True, verbose_name='表单描述')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    is_formio = models.BooleanField(default=False, verbose_name='是否使用FormIO')
    start_time = models.DateTimeField(verbose_name='开始报名时间')
    end_time = models.DateTimeField(verbose_name='结束报名时间')
    conference = models.ForeignKey(Conference, on_delete=models.SET_NULL, 
                                 related_name='registration_forms', 
                                 verbose_name='关联会议',
                                 null=True, blank=True)
    fields_json = models.JSONField(verbose_name='表单字段JSON', null=True, blank=True)
    logic_rules_json = models.JSONField(verbose_name='逻辑规则JSON', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '报名表单'
        verbose_name_plural = '报名表单'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError('结束时间必须晚于开始时间')

class FormField(models.Model):
    """表单字段定义"""
    FIELD_TYPES = (
        ('text', '单行文本'),
        ('textarea', '多行文本'),
        ('number', '数字'),
        ('select', '下拉选择'),
        ('radio', '单选'),
        ('checkbox', '多选'),
        ('date', '日期'),
        ('time', '时间'),
        ('file', '文件上传'),
    )

    form = models.ForeignKey(RegistrationForm, on_delete=models.CASCADE, 
                            related_name='fields', verbose_name='所属表单')
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES, verbose_name='字段类型')
    label = models.CharField(max_length=100, verbose_name='字段标签')
    name = models.CharField(max_length=100, verbose_name='字段名称')
    placeholder = models.CharField(max_length=200, null=True, blank=True, 
                                 verbose_name='占位文本')
    help_text = models.CharField(max_length=200, null=True, blank=True, 
                               verbose_name='帮助文本')
    required = models.BooleanField(default=True, verbose_name='是否必填')
    order = models.IntegerField(verbose_name='显示顺序')
    validation_regex = models.CharField(max_length=200, null=True, blank=True, 
                                      verbose_name='验证规则')
    error_message = models.CharField(max_length=200, null=True, blank=True, 
                                   verbose_name='错误提示')
    default_value = models.CharField(max_length=200, null=True, blank=True, 
                                   verbose_name='默认值')
    is_unique_in_company = models.BooleanField(default=False, 
                                              verbose_name='公司内唯一')
    max_occurrences = models.IntegerField(null=True, blank=True, 
                                        verbose_name='最大出现次数')

    class Meta:
        verbose_name = '表单字段'
        verbose_name_plural = '表单字段'
        ordering = ['order']
        unique_together = ['form', 'name']

    def __str__(self):
        return f"{self.form.title} - {self.label}"

class FieldOption(models.Model):
    """字段选项（用于下拉、单选、多选等）"""
    field = models.ForeignKey(FormField, on_delete=models.CASCADE, 
                             related_name='options', verbose_name='所属字段')
    label = models.CharField(max_length=100, verbose_name='选项标签')
    value = models.CharField(max_length=100, verbose_name='选项值')
    order = models.IntegerField(verbose_name='显示顺序')
    is_exclusive = models.BooleanField(default=False, verbose_name='是否互斥')
    max_selections = models.IntegerField(null=True, blank=True, 
                                       verbose_name='最大选择次数')

    class Meta:
        verbose_name = '字段选项'
        verbose_name_plural = '字段选项'
        ordering = ['order']

    def __str__(self):
        return f"{self.field.label} - {self.label}"

class FieldLogicRule(models.Model):
    """字段逻辑规则"""
    OPERATORS = (
        ('equals', '等于'),
        ('not_equals', '不等于'),
        ('contains', '包含'),
        ('not_contains', '不包含'),
        ('greater_than', '大于'),
        ('less_than', '小于'),
        ('in', '在列表中'),
        ('not_in', '不在列表中'),
        ('starts_with', '以...开头'),
        ('ends_with', '以...结尾'),
        ('is_empty', '为空'),
        ('is_not_empty', '不为空'),
        ('between', '在...之间'),
    )

    ACTIONS = (
        ('show', '显示'),
        ('hide', '隐藏'),
        ('enable', '启用'),
        ('disable', '禁用'),
        ('require', '必填'),
        ('unrequire', '非必填'),
        ('set_value', '设置值'),
        ('clear_value', '清除值'),
    )

    form = models.ForeignKey(RegistrationForm, on_delete=models.CASCADE,
                            related_name='logic_rules', verbose_name='所属表单')
    trigger_field = models.ForeignKey(FormField, on_delete=models.CASCADE,
                                    related_name='trigger_rules',
                                    verbose_name='触发字段',
                                    null=True)  # 临时允许为空，以便迁移
    operator = models.CharField(max_length=20, choices=OPERATORS,
                              verbose_name='运算符')
    value = models.JSONField(null=True, blank=True, verbose_name='比较值')
    target_field = models.ForeignKey(FormField, on_delete=models.CASCADE,
                                   related_name='target_rules',
                                   verbose_name='目标字段')
    action = models.CharField(max_length=20, choices=ACTIONS,
                            verbose_name='执行动作')
    action_value = models.JSONField(null=True, blank=True,
                                  verbose_name='动作值')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    condition_group = models.CharField(max_length=50, null=True, blank=True,
                                    verbose_name='条件组')
    priority = models.IntegerField(default=0, verbose_name='优先级')

    class Meta:
        verbose_name = '字段逻辑规则'
        verbose_name_plural = '字段逻辑规则'
        ordering = ['priority']

    def __str__(self):
        return f"{self.trigger_field.label} {self.get_operator_display()} -> {self.target_field.label} {self.get_action_display()}"

    def clean(self):
        if self.trigger_field.form_id != self.form_id:
            raise ValidationError('触发字段必须属于同一个表单')
        if self.target_field.form_id != self.form_id:
            raise ValidationError('目标字段必须属于同一个表单')
        if self.trigger_field_id == self.target_field_id:
            raise ValidationError('触发字段和目标字段不能相同')

class Registration(models.Model):
    """报名记录"""
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE,
                                 related_name='registrations', verbose_name='会议',
                                 null=True, blank=True)
    form = models.ForeignKey(RegistrationForm, on_delete=models.CASCADE, 
                            related_name='registrations', verbose_name='报名表单')
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, 
                                  related_name='registrations', 
                                  verbose_name='参会人员')
    contact_person = models.ForeignKey(ContactPerson, on_delete=models.CASCADE,
                                     related_name='submitted_registrations', 
                                     verbose_name='提交人')
    status = models.CharField(max_length=20, choices=(
        ('pending', '待审核'),
        ('confirmed', '已确认'),
        ('rejected', '已拒绝'),
        ('cancelled', '已取消'),
        ('checked_in', '已签到'),
    ), default='pending', verbose_name='状态')
    data = models.JSONField(verbose_name='表单数据')
    submitted_at = models.DateTimeField(auto_now_add=True, 
                                      verbose_name='提交时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '报名记录'
        verbose_name_plural = '报名记录'
        ordering = ['-submitted_at']
        unique_together = ['conference', 'participant']

    def __str__(self):
        return f"{self.participant} - {self.conference}"

    def clean(self):
        from django.utils import timezone
        now = timezone.now()
        if now < self.form.start_time:
            raise ValidationError('报名未开始')
        if now > self.form.end_time:
            raise ValidationError('报名已结束')

        if self.conference and self.participant:
            # 检查是否超过会议总人数限制
            if not self.conference.can_register():
                raise ValidationError('会议报名人数已达上限')
            
            # 检查是否超过公司人数限制
            if not self.conference.can_company_register(self.participant.company):
                raise ValidationError('贵公司的报名人数已达上限')

class FormResponse(models.Model):
    """表单回复"""
    form = models.ForeignKey(RegistrationForm, on_delete=models.CASCADE,
                            related_name='responses', verbose_name='表单')
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE,
                                  related_name='form_responses', verbose_name='参会人员')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '表单回复'
        verbose_name_plural = '表单回复'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.form.title} - {self.participant.name}"

class FormFieldResponse(models.Model):
    """表单字段回复"""
    response = models.ForeignKey(FormResponse, on_delete=models.CASCADE,
                               related_name='field_responses', verbose_name='表单回复')
    field = models.ForeignKey(FormField, on_delete=models.CASCADE,
                            related_name='responses', verbose_name='字段')
    value = models.TextField(verbose_name='回复内容')

    class Meta:
        verbose_name = '表单字段回复'
        verbose_name_plural = '表单字段回复'

    def __str__(self):
        return f"{self.response.form.title} - {self.field.label}"
