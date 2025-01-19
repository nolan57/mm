from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def staff_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_staff or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        messages.error(request, '您没有权限执行此操作')
        return redirect('conference:dashboard')
    return _wrapped_view

def participant_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request.user, 'participant'):
            messages.error(request, '您需要是参会人才能访问此页面。')
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return _wrapped_view
