from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from django.urls import reverse
from ..models.registration import RegistrationForm
from ..models.conference import Conference
from ..models import (
    FormField, FieldOption,
    Registration, Participant, Company, ContactPerson
)

@login_required
def manage_registration_forms(request):
    """Manage registration forms."""
    registration_forms = RegistrationForm.objects.all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            # Create a new registration form
            title = request.POST.get('title')
            description = request.POST.get('description')
            max_participants = request.POST.get('max_participants', 1)
            conference_id = request.POST.get('conference_id')

            conference = get_object_or_404(Conference, id=conference_id)
            RegistrationForm.objects.create(
                title=title,
                description=description,
                max_participants=max_participants,
                conference=conference
            )
            messages.success(request, '报名表单创建成功！')
            return redirect('conference:manage_registration_forms')
        
        elif action == 'delete':
            form_id = request.POST.get('form_id')
            registration_form = get_object_or_404(RegistrationForm, id=form_id)
            registration_form.delete()
            messages.success(request, '报名表单删除成功！')
            return redirect('conference:manage_registration_forms')

    return render(request, 'conferenceApp/registration/manage_form.html', {
        'registration_forms': registration_forms,
    })

@login_required
def edit_registration_form(request, form_id):
    """Edit an existing registration form."""
    registration_form = get_object_or_404(RegistrationForm, id=form_id)
    conferences = Conference.objects.all()
    
    # Add debug print
    print(f"Loading form {form_id}: title={registration_form.title}, description={registration_form.description}")
    print(f"Fields JSON: {registration_form.fields_json}")  # Add this line
    
    if request.method == 'POST':
        try:
            registration_form.title = request.POST.get('title', '').strip()
            registration_form.description = request.POST.get('description', '').strip()
            
            # 处理会议关联
            conference_id = request.POST.get('conference')
            if conference_id:
                registration_form.conference = get_object_or_404(Conference, id=conference_id)
            else:
                registration_form.conference = None
            
            # 处理表单字段数据
            fields = request.POST.get('fields')
            if fields:
                print(f"Received fields data: {fields}")  # Add debug logging
                registration_form.fields_json = fields
            
            # 处理逻辑规则数据
            logic_rules = request.POST.get('logic_rules')
            if logic_rules:
                print(f"Received logic rules data: {logic_rules}")  # Add debug logging
                registration_form.logic_rules_json = logic_rules
            
            registration_form.save()
            
            return JsonResponse({
                'success': True,
                'message': '报名表单更新成功！',
                'redirect_url': reverse('conference:manage_registration_forms')
            })
        except Exception as e:
            print(f"Error saving form: {str(e)}")  # Add error logging
            return JsonResponse({
                'success': False,
                'message': f'保存失败：{str(e)}'
            }, status=400)

    context = {
        'registration_form': registration_form,
        'conferences': conferences,
    }
    print(f"Context data: {context}")  # Add context logging
    return render(request, 'conferenceApp/registration/edit_form.html', context)

@login_required
def create_registration_form(request):
    """Create a new registration form."""
    if request.method == 'POST':
        try:
            # 获取基本信息
            title = request.POST.get('title')
            description = request.POST.get('description')
            form_fields = request.POST.get('fields')  # Changed from 'formFields' to 'fields'
            conference_id = request.POST.get('conference')
            is_formio = request.POST.get('is_formio', 'false').lower() == 'true'

            print(f"Creating form with title: {title}, description: {description}")
            print(f"Form fields: {form_fields}")
            print(f"Conference ID: {conference_id}")

            # 创建表单
            registration_form = RegistrationForm.objects.create(
                title=title,
                description=description,
                start_time=timezone.now(),
                end_time=timezone.now() + timezone.timedelta(days=30),
                is_formio=is_formio
            )

            print(f"Form created with ID: {registration_form.id}")

            # 如果选择了会议，关联会议
            if conference_id:
                try:
                    conference = Conference.objects.get(id=conference_id)
                    registration_form.conference = conference
                    registration_form.save()
                    print(f"Associated with conference: {conference.name}")
                except Conference.DoesNotExist:
                    print("Conference not found")
                    pass  # 如果会议不存在，就不关联

            # 保存表单字段
            if form_fields:
                # 这里可以处理form_fields的保存
                # form_fields 是一个JSON字符串，包含所有字段信息
                registration_form.fields_json = form_fields
                registration_form.save()
                print("Form fields saved")

            return JsonResponse({
                'success': True,
                'message': '报名表单创建成功！',
                'redirect_url': reverse('conference:manage_registration_forms')
            })
        except Exception as e:
            print(f"Error creating form: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'创建失败：{str(e)}'
            }, status=400)

    # 获取所有会议供选择
    conferences = Conference.objects.all()
    return render(request, 'conferenceApp/registration/create_form.html', {
        'conferences': conferences
    })

@login_required
def delete_registration_form(request, form_id):
    """删除报名表单"""
    if request.method == 'POST':
        try:
            registration_form = get_object_or_404(RegistrationForm, id=form_id)
            
            # 检查是否有关联的报名记录
            if registration_form.registrations.exists():
                return JsonResponse({
                    'success': False,
                    'message': '该表单已有报名记录，无法删除'
                }, status=400)
            
            # 删除表单
            registration_form.delete()
            
            return JsonResponse({
                'success': True,
                'message': '报名表单删除成功！'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'删除失败：{str(e)}'
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'message': '不支持的请求方法'
    }, status=405)

@login_required
def associate_conference(request):
    """关联会议和报名表单"""
    if request.method == 'POST':
        try:
            form_id = request.POST.get('form_id')
            conference_id = request.POST.get('conference')
            
            registration_form = get_object_or_404(RegistrationForm, id=form_id)
            conference = get_object_or_404(Conference, id=conference_id)
            
            # 更新关联关系
            registration_form.conference = conference
            registration_form.save()
            
            return JsonResponse({
                'success': True,
                'message': '关联成功！'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'关联失败：{str(e)}'
            }, status=400)
    
    return JsonResponse({
        'success': False,
        'message': '不支持的请求方法'
    }, status=405)

@login_required
def notify_suppliers(request, conference_id):
    """发送报名通知给供应商联系人"""
    conference = get_object_or_404(Conference, pk=conference_id)
    if request.method == 'POST':
        companies = Company.objects.filter(
            id__in=request.POST.getlist('companies')
        )
        
        for company in companies:
            contacts = ContactPerson.objects.filter(company=company)
            for contact in contacts:
                # 生成报名链接
                registration_url = request.build_absolute_uri(
                    f'/conference/{conference.id}/register/'
                )
                
                # 准备邮件内容
                context = {
                    'contact': contact,
                    'conference': conference,
                    'registration_url': registration_url
                }
                email_html = render_to_string(
                    'conferenceApp/emails/registration_invitation.html',
                    context
                )
                email_text = render_to_string(
                    'conferenceApp/emails/registration_invitation.txt',
                    context
                )
                
                # 发送邮件
                send_mail(
                    subject=f'{conference.name} - 会议报名通知',
                    message=email_text,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[contact.email],
                    html_message=email_html
                )
        
        messages.success(request, '报名通知已发送')
        return redirect('conference_detail', pk=conference_id)
    
    context = {
        'conference': conference,
        'companies': Company.objects.all()
    }
    return render(request, 'conferenceApp/registration/notify_suppliers.html', context)

@login_required
def submit_registration(request, conference_id):
    """提交会议报名"""
    conference = get_object_or_404(Conference, pk=conference_id)
    registration_form = get_object_or_404(RegistrationForm, conference=conference)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 创建或更新参会者信息
                participant_data = {
                    'name': request.POST.get('name'),
                    'company': request.user.contactperson.company,
                    'position': request.POST.get('position'),
                    'phone': request.POST.get('phone'),
                    'email': request.POST.get('email')
                }
                participant, created = Participant.objects.update_or_create(
                    registration_number=request.POST.get('registration_number', None),
                    defaults=participant_data
                )
                
                # 创建报名记录
                registration = Registration.objects.create(
                    conference=conference,
                    participant=participant,
                    form=registration_form,
                    submitted_by=request.user,
                    status='pending'
                )
                
                # 保存表单字段答案
                for field in registration_form.fields.all():
                    value = request.POST.get(f'field_{field.id}')
                    if field.field_type == 'checkbox':
                        value = ','.join(request.POST.getlist(f'field_{field.id}'))
                    registration.answers.create(field=field, value=value)
                
                messages.success(request, '报名提交成功，请等待审核')
                return redirect('registration_confirmation', registration_id=registration.id)
                
        except Exception as e:
            messages.error(request, f'报名提交失败：{str(e)}')
            return redirect('submit_registration', conference_id=conference_id)
    
    context = {
        'conference': conference,
        'registration_form': registration_form
    }
    return render(request, 'conferenceApp/registration/submit_form.html', context)

@login_required
def registration_confirmation(request, registration_id):
    """报名确认页面"""
    registration = get_object_or_404(Registration, pk=registration_id)
    context = {
        'registration': registration
    }
    return render(request, 'conferenceApp/registration/confirmation.html', context)
