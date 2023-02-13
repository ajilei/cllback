# coding=utf-8
import os
import copy as cp
import pandas as pd
import datetime
import json

from django.http import HttpResponse

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject2.settings')

import django

django.setup()

from django.db.models import Q

from TEAM.models import TeamModel
from USER.models import UserModel
from async_tasks.schedules.tasks import onteamupdate
import re
# 接口函数
def OneTeamMergeAPIView(request):
    print(request.method)
    if request.method == 'POST':  # 当提交表单时
        if request.POST:
            start_time = datetime.datetime.strptime(request.POST.get('start_time'), "%Y-%m-%d %H:%M")
            end_time = datetime.datetime.strptime(request.POST.get('end_time'), "%Y-%m-%d %H:%M")
            email = request.POST.get('email', '')
            onteamupdate.delay(start_time, end_time, email)
            data = {'email': email,
                    'start_time': str(start_time),
                    'end_time': str(end_time),
                    'code': 200,
                    'msg': email + '邮件发送成功,请稍等1分钟,如果3分钟内不能获取请联系管理员'}
            return HttpResponse(json.dumps(data))


def OneTeam(request):
    if request.method == 'POST':  # 当提交表单时
        company = TeamModel.objects.filter(parent=None)
        one_team = TeamModel.objects.filter(parent__in=company)
        two_team = TeamModel.objects.filter(parent__in=one_team)
        result = [['英文名', '中文名', '团队', '角色', '邮箱', '手机号', '加入时间', '离职时间', '是否为领导', '状态']]
        Q1 = Q(team__in=two_team) if request.POST.get('status', 0) == "所有" else Q(team__in=two_team, status='Active')
        user = UserModel.objects.filter(Q1).values('name', 'chineseName', 'team__name', 'email',
                                                   'title__name',
                                                   'email', 'mobile', 'joinDate', 'leaveDate',
                                                   'isleader',
                                                   'status')
        for i in user:
            join, leave, leader = None, None, None
            if i['isleader'] and i['isleader'] == 1:
                leader = 'leader'
            else:
                leader = '非leader'
            join = str(i['joinDate'])
            leave = str(i['leaveDate'])
            result.append(
                [i['name'], i['chineseName'], i['team__name'], i['title__name'], i['email'], i['mobile'], join,
                 leave, leader, i['status']])
        df = pd.DataFrame(result)
        name = '一级团队成员' + str(datetime.datetime.now()) + '.xlsx'
        name=re.sub(r' ','-',name)
        df.to_excel(name, index=False, header=None)
        data = {
            'code': 200,
            'msg': '下载成功',
            'file': name
        }
        return HttpResponse(json.dumps(data))


def error(request):
    a = 1
    a.split('---')
    return HttpResponse([a, b, c])
