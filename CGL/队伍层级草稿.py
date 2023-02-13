import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject2.settings')

import django

django.setup()

from django.db.models import Sum
from django.db.models import Q, F

from TEAM.models import TeamModel
from USER.models import UserModel
from INVOICE.models import InvoiceModel
from INVOICE.models import MoneyClientModel

from tool.decorator_tool import timmer
from tool.list_tool import open_list


# 拿层级队伍下面所有人id，后续使用需要增加过滤条件,暂时没用到，先留着
class teamUser(object):
    def __init__(self):
        all_user = TeamModel.objects.filter().order_by('id')
        one = TeamModel.objects.filter(parent=None, is_deleted=False).order_by('id')
        two = TeamModel.objects.filter(parent__in=one, is_deleted=False).order_by('id')
        three = TeamModel.objects.filter(parent__in=two, is_deleted=False).order_by('id')
        four = TeamModel.objects.filter(parent__in=three, is_deleted=False).order_by('id')
        five = TeamModel.objects.filter(parent__in=four, is_deleted=False).order_by('id')
        self.mapping = [all_user, one, two, three, four, five]

    def user(self, num):
        # 返queryset
        return self.mapping[num]

    def teamTree(self, num):
        if num == 1:
            return [i['id'] for i in self.mapping[0].values('id')]
        if num == 5:
            return [i['id'] for i in self.mapping[5].values('id')]
        id_list = []
        for i in [i for i in range(num, 6)]:
            id_list += [j['id'] for j in self.mapping[i].values('id')]
        return sorted(id_list)

