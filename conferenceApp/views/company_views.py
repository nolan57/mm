from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import user_passes_test
import pandas as pd

from ..models.company import Company
from ..models.contact import ContactPerson
from ..decorators import staff_required

def is_staff_or_admin(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_staff_or_admin)
def company_list(request):
    # 获取筛选参数
    name = request.GET.get('name', '')
    code = request.GET.get('code', '')
    business_type = request.GET.get('business_type', '')

    # 构建查询条件
    query = Q()
    if name:
        query &= Q(name__icontains=name)
    if code:
        query &= Q(code__icontains=code)
    if business_type:
        query &= Q(business_type__icontains=business_type)

    # 获取公司列表
    companies = Company.objects.filter(query).order_by('-created_at')

    # 分页
    paginator = Paginator(companies, 10)
    page = request.GET.get('page')
    companies = paginator.get_page(page)

    return render(request, 'conferenceApp/company/company_list.html', {
        'companies': companies,
        'filters': {
            'name': name,
            'code': code,
            'business_type': business_type
        }
    })

@login_required
@user_passes_test(is_staff_or_admin)
def create_company(request):
    if request.method == 'POST':
        try:
            company = Company.objects.create(
                name=request.POST['name'],
                code=request.POST['code'],
                business_type=request.POST['business_type'],
                address=request.POST.get('address', '')
            )
            messages.success(request, '公司创建成功')
            return redirect('company:list')
        except Exception as e:
            messages.error(request, f'创建失败：{str(e)}')
            return render(request, 'conferenceApp/company/company_form.html', {
                'form_type': 'create',
                'company': request.POST
            })

    return render(request, 'conferenceApp/company/company_form.html', {
        'form_type': 'create'
    })

@login_required
@user_passes_test(is_staff_or_admin)
def update_company(request, pk):
    company = get_object_or_404(Company, pk=pk)
    
    if request.method == 'POST':
        try:
            company.name = request.POST['name']
            company.code = request.POST['code']
            company.business_type = request.POST['business_type']
            company.address = request.POST.get('address', '')
            company.save()
            messages.success(request, '公司信息更新成功')
            return redirect('company:list')
        except Exception as e:
            messages.error(request, f'更新失败：{str(e)}')
            return render(request, 'conferenceApp/company/company_form.html', {
                'form_type': 'update',
                'company': company
            })

    return render(request, 'conferenceApp/company/company_form.html', {
        'form_type': 'update',
        'company': company
    })

@login_required
@user_passes_test(is_staff_or_admin)
def delete_company(request, pk):
    try:
        company = Company.objects.get(pk=pk)
        company.delete()
        return JsonResponse({'status': 'success', 'message': '公司删除成功'})
    except Company.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': '公司不存在'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

@login_required
@staff_required
@require_POST
def import_companies(request):
    if 'file' not in request.FILES:
        return JsonResponse({'status': 'error', 'message': '请选择要导入的文件'})

    try:
        excel_file = request.FILES['file']
        df = pd.read_excel(excel_file)
        
        required_columns = ['公司名称', '公司编码', '业务类型', '公司地址']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return JsonResponse({
                'status': 'error',
                'message': f'文件缺少必要的列：{", ".join(missing_columns)}'
            })

        success_count = 0
        error_count = 0
        errors = []

        for _, row in df.iterrows():
            try:
                if Company.objects.filter(code=row['公司编码']).exists():
                    error_count += 1
                    errors.append(f"公司编码 {row['公司编码']} 已存在")
                    continue

                Company.objects.create(
                    name=row['公司名称'],
                    code=row['公司编码'],
                    business_type=row['业务类型'],
                    address=row['公司地址']
                )
                success_count += 1
            except Exception as e:
                error_count += 1
                errors.append(f"导入 {row['公司名称']} 时出错：{str(e)}")

        return JsonResponse({
            'status': 'success',
            'message': f'成功导入 {success_count} 家公司，失败 {error_count} 家',
            'errors': errors
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'导入失败：{str(e)}'
        })

@login_required
@staff_required
def manage_contacts(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    contacts = ContactPerson.objects.filter(company=company)
    return render(request, 'conferenceApp/company/contacts.html', {
        'company': company,
        'contacts': contacts,
    })
