import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject2.settings')

import django

django.setup()

from TEAM.models import TeamModel
from USER.models import UserModel
import pandas as pd

company = TeamModel.objects.filter(parent=None)
one_team = TeamModel.objects.filter(parent__in=company)
two_team = TeamModel.objects.filter(parent__in=one_team)

result = [['英文名', '中文名', '团队', '角色', '邮箱', '手机号', '加入时间', '离职时间', '是否为领导', '状态']]
user = UserModel.objects.filter(team__in=two_team).values('name', 'chineseName', 'team__name', 'email', 'title__name',
                                                          'email', 'mobile', 'joinDate', 'leaveDate','isleader', 'status')
for i in user:
    join, leave,leader = None, None,None
    if i['isleader']:
        leader = i['isleader']
    join =i['joinDate']
    leave =i['leaveDate']
    result.append(
        [i['name'], i['chineseName'], i['team__name'], i['title__name'], i['email'], i['mobile'], join,
         leave, i['isleader'], i['status']])
df = pd.DataFrame(result)
df.to_excel('一级团队成员.xlsx', index=False, header=None)
