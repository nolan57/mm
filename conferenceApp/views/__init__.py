from .registration_views import (
    conference_register, registration_list,
    registration_approve, registration_cancel,
    company_registration_manage, add_participant,
    remove_participant
)

from .conference_views import (
    ConferenceListView, ConferenceCreateView,
    ConferenceUpdateView, ConferenceDeleteView,
    conference_detail, conference_edit,
    conference_delete, DashboardView,
    ConferenceManagementView
)

from .form_views import manage_form, set_current_form
from .participant import ParticipantManagementView

__all__ = [
    # Registration views
    'conference_register',
    'registration_list',
    'registration_approve',
    'registration_cancel',
    'company_registration_manage',
    'add_participant',
    'remove_participant',
    
    # Conference views
    'ConferenceListView',
    'ConferenceCreateView',
    'ConferenceUpdateView',
    'ConferenceDeleteView',
    'DashboardView',
    'ConferenceManagementView',
    'conference_detail',
    'conference_edit',
    'conference_delete',
    'manage_form',
    'set_current_form',
    
    # Participant views
    'ParticipantManagementView',
]
