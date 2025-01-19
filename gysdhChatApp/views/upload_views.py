import os
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
import uuid

@csrf_protect
@require_http_methods(["POST"])
def upload_image(request):
    if 'image' not in request.FILES:
        return JsonResponse({'error': 'No image file'}, status=400)
    
    image_file = request.FILES['image']
    
    # 验证文件类型
    allowed_types = ['image/jpeg', 'image/png', 'image/gif']
    if image_file.content_type not in allowed_types:
        return JsonResponse({'error': 'Invalid file type'}, status=400)
    
    # 生成唯一文件名
    ext = os.path.splitext(image_file.name)[1]
    filename = f"{uuid.uuid4()}{ext}"
    
    # 确保上传目录存在
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', 'images')
    os.makedirs(upload_dir, exist_ok=True)
    
    # 保存文件
    filepath = os.path.join(upload_dir, filename)
    with open(filepath, 'wb+') as destination:
        for chunk in image_file.chunks():
            destination.write(chunk)
    
    # 返回URL
    url = f"{settings.MEDIA_URL}uploads/images/{filename}"
    return JsonResponse({'url': url})
