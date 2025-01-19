from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
import csv
from datetime import datetime
from ..models import Conference, Registration, Company, Participant

class ParticipantManagementView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'conferenceApp/participant_management.html'
    context_object_name = 'registrations'
    paginate_by = 20

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_admin

    def get_queryset(self):
        queryset = Registration.objects.select_related(
            'conference', 'participant', 'contact_person', 
            'contact_person__company'
        ).order_by('-submitted_at')

        # 搜索过滤
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(participant__name__icontains=search) |
                Q(contact_person__company__name__icontains=search) |
                Q(participant__phone__icontains=search)
            )

        # 会议过滤
        conference_id = self.request.GET.get('conference')
        if conference_id:
            queryset = queryset.filter(conference_id=conference_id)

        # 状态过滤
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['conferences'] = Conference.objects.all().order_by('-start_date')
        context['total_participants'] = Registration.objects.count()
        # 获取所有注册记录关联的公司
        context['total_companies'] = Company.objects.filter(
            contacts__submitted_registrations__isnull=False
        ).distinct().count()
        context['confirmed_participants'] = Registration.objects.filter(
            status='confirmed'
        ).count()
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        registration_id = request.POST.get('registration_id')

        if not registration_id:
            return JsonResponse({'success': False, 'message': '参数错误'}, status=400)

        registration = get_object_or_404(Registration, id=registration_id)

        if action == 'update_status':
            status = request.POST.get('status')
            if status not in ['pending', 'confirmed', 'cancelled']:
                return JsonResponse({'success': False, 'message': '状态无效'}, status=400)
            
            registration.status = status
            registration.save()
            return JsonResponse({
                'success': True,
                'message': '状态更新成功',
                'status': registration.get_status_display()
            })

        elif action == 'delete':
            try:
                registration.delete()
                return JsonResponse({
                    'success': True,
                    'message': '参会人删除成功'
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'删除失败：{str(e)}'
                }, status=400)

        return JsonResponse({'success': False, 'message': '未知操作'}, status=400)

def export_participants(request):
    """导出参会人数据为CSV文件"""
    if not (request.user.is_staff or request.user.is_admin):
        messages.error(request, '您没有权限执行此操作')
        return redirect('conference:dashboard')

    # 获取筛选条件
    conference_id = request.GET.get('conference')
    status = request.GET.get('status')
    search = request.GET.get('search')

    # 构建查询
    queryset = Registration.objects.select_related(
        'conference', 'participant', 'contact_person',
        'contact_person__company'
    )

    if conference_id:
        queryset = queryset.filter(conference_id=conference_id)
    if status:
        queryset = queryset.filter(status=status)
    if search:
        queryset = queryset.filter(
            Q(participant__name__icontains=search) |
            Q(contact_person__company__name__icontains=search) |
            Q(participant__phone__icontains=search)
        )

    # 创建CSV响应
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="participants_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        '会议名称', '单位名称', '姓名', '职位',
        '联系电话', '电子邮箱', '状态', '提交时间'
    ])

    for registration in queryset:
        writer.writerow([
            registration.conference.name,
            registration.contact_person.company.name,
            registration.participant.name,
            registration.participant.position,
            registration.participant.phone,
            registration.participant.email,
            registration.get_status_display(),
            registration.submitted_at.strftime('%Y-%m-%d %H:%M:%S')
        ])

    return response
