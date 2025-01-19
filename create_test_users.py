from conferenceApp.models import Company
from gysdhChatApp.models import User, UserGroup

# 获取公司
company1 = Company.objects.get(code='A001')
company2 = Company.objects.get(code='B001')

# 获取用户组
contact_group, _ = UserGroup.objects.get_or_create(
    name='联系人',
    defaults={'description': '公司联系人，负责报名和管理参会人员'}
)

staff_group, _ = UserGroup.objects.get_or_create(
    name='工作人员',
    defaults={'description': '会议工作人员，负责会议现场管理'}
)

# 创建用户
users_data = [
    {
        'name': '用户B1',
        'company': company2,
        'email': 'user777777@example.com',
        'password': 'uu585858',
        'number': '777777',
        'group': contact_group,
        'position': '联系人',
        'phone': '13900139001',
        'can_publish_announcements': False,
        'can_private_message': True,
        'is_event_staff': False
    }
]

for data in users_data:
    # 创建用户
    user = User.objects.create_user(
        name=data['name'],
        company=data['company'],
        email=data['email'],
        password=data['password'],
        number=data['number']
    )
    # 设置用户组和权限
    user.group = data['group']
    user.position = data['position']
    user.phone = data['phone']
    user.can_publish_announcements = data['can_publish_announcements']
    user.can_private_message = data['can_private_message']
    user.is_event_staff = data['is_event_staff']
    if 'is_admin' in data:
        user.is_admin = data['is_admin']
    user.save()
    
    print(f'Created user {user.name} with number {user.number} as {data["group"].name}')
