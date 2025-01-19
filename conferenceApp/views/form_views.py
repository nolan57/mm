from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseForbidden
from django.db import transaction

from ..models import Conference, RegistrationForm

@login_required
@user_passes_test(lambda u: u.is_staff)
def manage_form(request):
    """报名表单管理视图"""
    # 获取所有表单和会议
    registration_forms = RegistrationForm.objects.all().order_by('-created_at')
    conferences = Conference.objects.all().order_by('-created_at')
    
    context = {
        'title': '报名表单管理',
        'subtitle': '管理会议报名表单和字段设置',
        'registration_forms': registration_forms,
        'conferences': conferences,
    }
    return render(request, 'conferenceApp/registration/manage_form.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def set_current_form(request):
    """设置会议当前使用的报名表单"""
    if request.method != 'POST':
        return HttpResponseForbidden()
        
    form_id = request.POST.get('form_id')
    conference_id = request.POST.get('conference_id')
    
    if not form_id or not conference_id:
        messages.error(request, '请选择表单和会议')
        return redirect('conference:manage_form')
    
    try:
        with transaction.atomic():
            form = get_object_or_404(RegistrationForm, id=form_id)
            conference = get_object_or_404(Conference, id=conference_id)
            
            # 更新会议的当前表单
            conference.registration_form = form
            conference.save()
            
            messages.success(request, f'已将 {form.name} 设置为 {conference.name} 的当前报名表单')
    except Exception as e:
        messages.error(request, f'设置当前表单时出错：{str(e)}')
    
    return redirect('conference:manage_form')
