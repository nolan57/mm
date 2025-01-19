from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import user_passes_test

from ..models.company import Company
from ..models.contact import ContactPerson
from ..models.conference import Conference
from ..decorators import staff_required
from gysdhChatApp.models import User
from ..models.contact import ContactTag

def is_staff_or_admin(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_staff_or_admin)
def contact_list(request):
    # 获取筛选参数
    name = request.GET.get('name', '')
    company = request.GET.get('company', '')
    position = request.GET.get('position', '')
    is_primary = request.GET.get('is_primary', '')

    # 构建查询条件
    filters = Q()
    if name:
        filters &= Q(user__name__icontains=name)
    if company:
        filters &= Q(company__name__icontains=company)
    if position:
        filters &= Q(position__icontains=position)
    if is_primary:
        filters &= Q(is_primary=True)

    # 获取联系人列表
    contacts = ContactPerson.objects.filter(filters).select_related('user', 'company')

    # 获取可用的用户列表（排除已经是联系人的用户）
    existing_user_ids = ContactPerson.objects.values_list('user_id', flat=True)
    available_users = User.objects.exclude(id__in=existing_user_ids).order_by('name')

    # 对可导入用户进行分页
    import_page_size = 10  # 每页显示的用户数量
    import_paginator = Paginator(available_users, import_page_size)
    import_page = request.GET.get('import_page', 1)
    try:
        available_users = import_paginator.page(import_page)
    except (Paginator.PageNotAnInteger, Paginator.EmptyPage):
        available_users = import_paginator.page(1)

    # 获取所有标签
    tags = ContactTag.objects.all()

    context = {
        'contacts': contacts,
        'filters': {
            'name': name,
            'company': company,
            'position': position,
            'is_primary': is_primary,
        },
        'available_users': available_users,
        'tags': tags,
    }

    # 如果是 AJAX 请求，只返回导入用户表单部分
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'conferenceApp/contact/import_users_form.html', context)

    # 分页
    paginator = Paginator(contacts, 10)
    page = request.GET.get('page')
    contacts = paginator.get_page(page)

    context['contacts'] = contacts

    return render(request, 'conferenceApp/contact/contact_list.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def create_contact(request):
    if request.method == 'POST':
        # 获取表单数据
        user_id = request.POST.get('user')
        position = request.POST.get('position')
        phone = request.POST.get('phone')
        email = request.POST.get('email')

        try:
            user = User.objects.get(pk=user_id)
            if not hasattr(user, 'company'):
                raise ValueError('所选用户未关联公司')

            # 创建联系人
            contact = ContactPerson.objects.create(
                company=user.company,
                user=user,
                position=position,
                phone=phone,
                email=email,
                is_primary=False  # 默认不设为主要联系人
            )
            messages.success(request, '联系人创建成功')
            return redirect('conference:contact_list')
        except User.DoesNotExist:
            messages.error(request, '所选用户不存在')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'创建失败：{str(e)}')
        return redirect('conference:contact_list')

    # GET 请求，显示表单
    # 只显示已关联公司且尚未成为联系人的用户
    existing_user_ids = ContactPerson.objects.values_list('user_id', flat=True)
    users = User.objects.filter(
        is_active=True,
        company__isnull=False
    ).exclude(
        id__in=existing_user_ids
    ).select_related('company')

    context = {
        'users': users,
    }
    return render(request, 'conferenceApp/contact/contact_form.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def update_contact(request, pk):
    contact = get_object_or_404(ContactPerson, pk=pk)

    if request.method == 'POST':
        # 获取表单数据
        position = request.POST.get('position')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        is_primary = request.POST.get('is_primary') == 'on'

        try:
            # 更新联系人信息
            contact.position = position
            contact.phone = phone
            contact.email = email
            contact.is_primary = is_primary
            contact.save()

            messages.success(request, '联系人信息更新成功')
            return redirect('conference:contact_list')
        except Exception as e:
            messages.error(request, f'更新失败：{str(e)}')

    # GET 请求，显示表单
    context = {
        'contact': contact,
    }
    return render(request, 'conferenceApp/contact/contact_form.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
@require_POST
def delete_contact(request, pk):
    contact = get_object_or_404(ContactPerson, pk=pk)
    try:
        contact.delete()
        messages.success(request, '联系人删除成功')
    except Exception as e:
        messages.error(request, f'删除失败：{str(e)}')
    return redirect('conference:contact_list')

@login_required
@user_passes_test(is_staff_or_admin)
def contact_detail(request, pk):
    contact = get_object_or_404(ContactPerson, pk=pk)
    # 获取该联系人参与的所有会议
    conference_contacts = contact.conference_roles.all().select_related('conference')
    
    context = {
        'contact': contact,
        'conference_contacts': conference_contacts,
    }
    return render(request, 'conferenceApp/contact/contact_detail.html', context)

@login_required
@user_passes_test(is_staff_or_admin)
def manage_conference_roles(request, contact_id):
    contact = get_object_or_404(ContactPerson, pk=contact_id)
    
    if request.method == 'POST':
        conference_id = request.POST.get('conference')
        role = request.POST.get('role')
        is_primary = request.POST.get('is_primary') == 'on'
        notes = request.POST.get('notes', '')

        try:
            conference = Conference.objects.get(pk=conference_id)
            # 创建或更新会议联系人角色
            conference_contact, created = ConferenceContact.objects.update_or_create(
                contact=contact,
                conference=conference,
                defaults={
                    'role': role,
                    'is_primary': is_primary,
                    'notes': notes,
                }
            )
            messages.success(request, '会议角色设置成功')
        except Exception as e:
            messages.error(request, f'设置失败：{str(e)}')

    # 获取所有会议
    conferences = Conference.objects.all()
    # 获取该联系人当前的会议角色
    current_roles = contact.conference_roles.all().select_related('conference')
    
    context = {
        'contact': contact,
        'conferences': conferences,
        'current_roles': current_roles,
    }
    return render(request, 'conferenceApp/contact/manage_roles.html', context)

@login_required
@staff_required
def delete_conference_role(request, pk):
    role = get_object_or_404(ConferenceRole, pk=pk)
    role.delete()
    messages.success(request, '会议角色已删除')
    return redirect('conference:manage_conference_roles')

@login_required
@user_passes_test(is_staff_or_admin)
@require_POST
def batch_delete_contacts(request):
    contact_ids = request.POST.get('contact_ids', '').split(',')
    if not contact_ids:
        messages.error(request, '请选择要删除的联系人')
        return redirect('conference:contact_list')

    try:
        ContactPerson.objects.filter(id__in=contact_ids).delete()
        messages.success(request, f'成功删除 {len(contact_ids)} 个联系人')
    except Exception as e:
        messages.error(request, f'删除联系人时出错：{str(e)}')

    return redirect('conference:contact_list')

@login_required
@user_passes_test(is_staff_or_admin)
@require_POST
def batch_assign_tags(request):
    contact_ids = request.POST.get('contact_ids', '').split(',')
    tag_id = request.POST.get('tag_id')
    action = request.GET.get('action', 'add')

    if not contact_ids or not tag_id:
        messages.error(request, '请选择联系人和标签')
        return redirect('conference:contact_list')

    try:
        tag = ContactTag.objects.get(id=tag_id)
        contacts = ContactPerson.objects.filter(id__in=contact_ids)
        
        if action == 'add':
            for contact in contacts:
                contact.tags.add(tag)
            messages.success(request, f'成功为 {len(contact_ids)} 个联系人添加标签 "{tag.name}"')
        else:
            for contact in contacts:
                contact.tags.remove(tag)
            messages.success(request, f'成功为 {len(contact_ids)} 个联系人移除标签 "{tag.name}"')
    except ContactTag.DoesNotExist:
        messages.error(request, '标签不存在')
    except Exception as e:
        messages.error(request, f'操作标签时出错：{str(e)}')

    return redirect('conference:contact_list')

@login_required
@user_passes_test(is_staff_or_admin)
@require_POST
def import_users(request):
    user_ids = request.POST.getlist('user_ids[]')
    if not user_ids:
        messages.error(request, '请选择要导入的用户')
        return redirect('conference:contact_list')

    try:
        users = User.objects.filter(id__in=user_ids)
        created_count = 0
        for user in users:
            # 检查用户是否已经是联系人
            if not ContactPerson.objects.filter(user=user).exists():
                ContactPerson.objects.create(
                    user=user,
                    email=user.email
                )
                created_count += 1

        if created_count > 0:
            messages.success(request, f'成功导入 {created_count} 个用户为联系人')
        else:
            messages.info(request, '所选用户已经都是联系人了')
    except Exception as e:
        messages.error(request, f'导入用户时出错：{str(e)}')

    return redirect('conference:contact_list')
