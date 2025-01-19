from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings
from django.db import transaction

from ..models.participant import Participant, ParticipantInfoChange
from ..decorators import participant_required, staff_required

def is_staff_or_admin(user):
    return user.is_staff or user.is_superuser

@login_required
@staff_required
def participant_list(request):
    """参会人列表视图"""
    # 获取筛选参数
    name = request.GET.get('name', '')
    company = request.GET.get('company', '')
    status = request.GET.get('status', '')
    verified = request.GET.get('verified', '')

    # 构建查询
    participants = Participant.objects.all()
    if name:
        participants = participants.filter(name__icontains=name)
    if company:
        participants = participants.filter(company__name__icontains=company)
    if status:
        participants = participants.filter(status=status)
    if verified:
        participants = participants.filter(info_verified=verified == 'true')

    return render(request, 'conferenceApp/participant/list.html', {
        'participants': participants,
        'filters': {
            'name': name,
            'company': company,
            'status': status,
            'verified': verified
        }
    })

@login_required
@staff_required
def create_participant_account(request, participant_id):
    """为参会人创建用户账号"""
    participant = get_object_or_404(Participant, id=participant_id)
    
    if participant.user:
        messages.error(request, '该参会人已有关联账号')
        return redirect('conference:participant_list')
    
    try:
        # 创建用户账号并获取临时密码
        temp_password = participant.create_user_account()
        if temp_password:
            # 发送账号信息邮件
            context = {
                'participant': participant,
                'temp_password': temp_password,
                'login_url': request.build_absolute_uri('/login/')
            }
            email_html = render_to_string('conferenceApp/emails/account_created.html', context)
            email_text = render_to_string('conferenceApp/emails/account_created.txt', context)
            
            send_mail(
                subject='您的参会系统账号已创建',
                message=email_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[participant.email],
                html_message=email_html
            )
            
            messages.success(request, f'已为 {participant.name} 创建账号并发送邮件通知')
        else:
            messages.error(request, '创建账号失败，请确保参会人有有效的邮箱地址')
    except Exception as e:
        messages.error(request, f'创建账号时出错：{str(e)}')
    
    return redirect('conference:participant_list')

@login_required
@participant_required
def participant_profile(request):
    """参会人个人信息页面"""
    participant = get_object_or_404(Participant, user=request.user)
    pending_changes = participant.info_changes.filter(status='pending')
    
    return render(request, 'conferenceApp/participant/profile.html', {
        'participant': participant,
        'pending_changes': pending_changes
    })

@login_required
@participant_required
def request_info_change(request):
    """申请信息变更"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'})
    
    participant = get_object_or_404(Participant, user=request.user)
    field_name = request.POST.get('field_name')
    new_value = request.POST.get('new_value')
    
    if not field_name or not new_value:
        return JsonResponse({'status': 'error', 'message': '缺少必要参数'})
    
    # 检查字段是否允许修改
    allowed_fields = ['name', 'position', 'phone', 'email']
    if field_name not in allowed_fields:
        return JsonResponse({'status': 'error', 'message': '该字段不允许修改'})
    
    try:
        # 创建变更申请
        change = participant.request_info_change(field_name, new_value, request.user)
        return JsonResponse({
            'status': 'success',
            'message': '变更申请已提交，请等待审核',
            'change_id': change.id
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
@staff_required
def review_info_change(request, change_id):
    """审核信息变更申请"""
    change = get_object_or_404(ParticipantInfoChange, id=change_id)
    
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'})
    
    action = request.POST.get('action')
    comment = request.POST.get('comment', '')
    
    if action not in ['approve', 'reject']:
        return JsonResponse({'status': 'error', 'message': '无效的操作'})
    
    try:
        with transaction.atomic():
            if action == 'approve':
                # 更新参会人信息
                setattr(change.participant, change.field_name, change.new_value)
                change.participant.save()
                change.status = 'approved'
            else:
                change.status = 'rejected'
            
            change.reviewed_by = request.user
            change.review_comment = comment
            change.save()
            
            # 发送邮件通知
            context = {
                'participant': change.participant,
                'change': change,
                'reviewer': request.user
            }
            email_html = render_to_string('conferenceApp/emails/info_change_reviewed.html', context)
            email_text = render_to_string('conferenceApp/emails/info_change_reviewed.txt', context)
            
            send_mail(
                subject='您的信息变更申请已审核',
                message=email_text,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[change.participant.email],
                html_message=email_html
            )
            
            return JsonResponse({
                'status': 'success',
                'message': '审核完成',
                'result': change.status
            })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
@participant_required
def send_verification_code(request):
    """发送验证码"""
    participant = get_object_or_404(Participant, user=request.user)
    
    try:
        # 生成验证码
        code = participant.generate_verification_code()
        
        # 发送验证码邮件
        context = {
            'participant': participant,
            'code': code,
            'expires_in': '30分钟'
        }
        email_html = render_to_string('conferenceApp/emails/verification_code.html', context)
        email_text = render_to_string('conferenceApp/emails/verification_code.txt', context)
        
        send_mail(
            subject='参会信息验证码',
            message=email_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[participant.email],
            html_message=email_html
        )
        
        return JsonResponse({
            'status': 'success',
            'message': '验证码已发送到您的邮箱'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
@participant_required
def verify_participant(request):
    """验证参会人信息"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': '无效的请求方法'})
    
    participant = get_object_or_404(Participant, user=request.user)
    code = request.POST.get('code')
    
    if not code:
        return JsonResponse({'status': 'error', 'message': '请输入验证码'})
    
    if participant.verify_code(code):
        return JsonResponse({
            'status': 'success',
            'message': '验证成功'
        })
    else:
        return JsonResponse({
            'status': 'error',
            'message': '验证码无效或已过期'
        })
