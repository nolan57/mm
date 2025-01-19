from conferenceApp.models import Company
from gysdhChatApp.models import User

# 创建两个公司
company1 = Company.objects.create(
    name='公司A',
    code='A001',
    business_type='manufacturer',
    address='北京市朝阳区'
)

company2 = Company.objects.create(
    name='公司B',
    code='B001',
    business_type='supplier',
    address='上海市浦东新区'
)

# 创建超级用户
superuser = User.objects.create_superuser(
    name='管理员',
    company=company1,
    email='admin@example.com',
    password='admin123',
    number='000000'
)

# 更新已有用户的公司关联
users_to_update = {
    '99999': company1,
    '888888': company1,
    '777777': company2
}

for number, company in users_to_update.items():
    try:
        user = User.objects.get(number=number)
        user.company = company
        user.save()
        print(f'Updated user {number} with company {company.name}')
    except User.DoesNotExist:
        print(f'User {number} not found')
