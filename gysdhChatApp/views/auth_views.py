from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect
from django.views import View
from conferenceApp.models import Conference

class LoginView(View):
    template_name = 'login.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        number = request.POST.get('number')
        password = request.POST.get('password')
        
        if not number.isdigit() or len(number) != 6:
            return render(request, self.template_name, {
                'error_message': 'Invalid ID format. Please enter a 6-digit number.'
            })
        
        user = authenticate(request, number=number, password=password)
        if user is not None:
            login(request, user)
            
            # 检查会议列表是否为空且用户是否有管理员权限
            if Conference.objects.count() == 0 and (user.is_admin):
                return redirect('conference:dashboard')  # 重定向到会议管理面板
                
            return redirect('conference:list')  # 重定向到会议列表页面
        
        return render(request, self.template_name, {
            'error_message': 'ID or password is incorrect'
        })


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('login')  # 登出后重定向到登录页面
