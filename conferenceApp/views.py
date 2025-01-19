from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Conference, Registration, Company

class ParticipantManagementView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    template_name = 'conferenceApp/participant_management.html'
    context_object_name = 'registrations'
    paginate_by = 20

    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_admin

    def get_queryset(self):
        queryset = Registration.objects.select_related(
            'conference', 'participant', 'company'
        ).order_by('-created_at')

        # 搜索过滤
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(participant__name__icontains=search) |
                Q(company__name__icontains=search) |
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
        context['total_companies'] = Company.objects.filter(
            id__in=Registration.objects.values('company_id')
        ).count()
        context['confirmed_participants'] = Registration.objects.filter(
            status='confirmed'
        ).count()
        return context
