from django.urls import path
from .views import (
    ConferenceListView, ConferenceCreateView, ConferenceUpdateView,
    ConferenceDeleteView, conference_detail, DashboardView, ConferenceManagementView,
    conference_register, company_registration_manage, add_participant, remove_participant,
    manage_form, set_current_form, conference_views, registration, company_views,
    ParticipantManagementView, participant
)
from .views.registration import (manage_registration_forms, edit_registration_form, create_registration_form, delete_registration_form, associate_conference)  # manage_registration_forms，edit_registration_form
from .views import contact_views
from .views import participant_views  # Added this line

app_name = 'conference'

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('create/', ConferenceCreateView.as_view(), name='create'),
    path('<int:pk>/', conference_detail, name='detail'),
    path('<int:pk>/edit/', ConferenceUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', ConferenceDeleteView.as_view(), name='delete'),
    path('management/', ConferenceManagementView.as_view(), name='management'),
    path('list/', ConferenceListView.as_view(), name='list'),
    path('<int:pk>/register/', conference_register, name='register'),
    path('<int:conference_id>/company-registration/', company_registration_manage, name='company_registration_manage'),
    path('<int:conference_id>/add-participant/', add_participant, name='add_participant'),
    path('registration/<int:registration_id>/remove/', remove_participant, name='remove_participant'),
    path('manage-form/', manage_form, name='manage_form'),  # 表单管理
    path('set-current-form/', set_current_form, name='set_current_form'),  # 设置当前表单
    path('manage-registration-forms/', manage_registration_forms, name='manage_registration_forms'),
    path('manage-registrations/', manage_registration_forms, name='manage_registration_forms'),
    path('edit-registration-form/<int:form_id>/', edit_registration_form, name='edit_registration_form'), 
    path('create-registration-form/', create_registration_form, name='create_registration_form'),  # Add this line
    path('delete-registration-form/<int:form_id>/', delete_registration_form, name='delete_registration_form'),  # 添加删除表单的 URL
    path('associate-conference/', associate_conference, name='associate_conference'),  # 添加关联会议的 URL

    # 公司管理
    path('companies/', company_views.company_list, name='company_list'),
    path('company/create/', company_views.create_company, name='create_company'),
    path('company/<int:pk>/update/', company_views.update_company, name='update_company'),
    path('company/<int:pk>/delete/', company_views.delete_company, name='delete_company'),
    path('company/<int:company_id>/contacts/', company_views.manage_contacts, name='manage_contacts'),
    path('company/import/', company_views.import_companies, name='import_companies'),
    
    # 参会人管理
    path('participants/', ParticipantManagementView.as_view(), name='participant_management'),
    path('participants/export/', participant.export_participants, name='export_participants'),
    path('participants/', participant_views.participant_list, name='participant_list'),
    path('participants/<int:participant_id>/create-account/', participant_views.create_participant_account, name='create_participant_account'),
    path('participant/profile/', participant_views.participant_profile, name='participant_profile'),
    path('participant/request-info-change/', participant_views.request_info_change, name='request_info_change'),
    path('participant/info-change/<int:change_id>/review/', participant_views.review_info_change, name='review_info_change'),
    path('participant/send-verification-code/', participant_views.send_verification_code, name='send_verification_code'),
    path('participant/verify/', participant_views.verify_participant, name='verify_participant'),

    # 联系人管理
    path('contacts/', contact_views.contact_list, name='contact_list'),
    path('contacts/create/', contact_views.create_contact, name='create_contact'),
    path('contacts/<int:pk>/', contact_views.contact_detail, name='contact_detail'),
    path('contacts/<int:pk>/update/', contact_views.update_contact, name='update_contact'),
    path('contacts/<int:pk>/delete/', contact_views.delete_contact, name='delete_contact'),
    path('contacts/<int:contact_id>/conference-roles/', contact_views.manage_conference_roles, name='manage_conference_roles'),
    path('conference-roles/<int:pk>/delete/', contact_views.delete_conference_role, name='delete_conference_role'),
    # 新增的批量操作路由
    path('contacts/batch-delete/', contact_views.batch_delete_contacts, name='batch_delete_contacts'),
    path('contacts/batch-assign-tags/', contact_views.batch_assign_tags, name='batch_assign_tags'),
    path('contacts/import-users/', contact_views.import_users, name='import_users'),
]
