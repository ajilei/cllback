import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject2.settings')

import django

django.setup()

from django.db.models import Sum

from TEAM.models import TeamModel
from INVOICE.models import InvoiceModel
from INVOICE.models import MoneyClientModel
from USER.models import UserModel

from tool.decorator_tool import timmer
from tool.list_tool import open_list


# status_dict = {
#     'feeCharge_sum': 'Billing业绩',
#     'invoiceAmount_sum': '开票金额',
#     'paymentReceived_sum': '到账金额'
# }


# 团队树
class TeamTree(object):
    def __teamSon(self, obj):
        display_list = []
        for i in obj:
            display_list.append(i.id)
            children = i.children.all()
            if len(children) > 0:
                display_list.append(self.__teamSon(children))
        return display_list

    # 输入Id，返回层级下所有队伍Id
    def teamTree(self, team_id):
        # go_out_user = UserModel.objects.filter(status='Leave').values('team_id'))exclude(name__contains='独立', id=go_out_user)
        init_team = TeamModel.objects.filter(id=team_id)
        return self.__teamSon(init_team)

    # 做了兼容，防止以后出现特殊不要的队伍，排除了名字中含独立的，离职的员工团队
    def filterTeam(self, team_id, no_need_id):
        all_team = self.teamTree(team_id)
        return [val for val in all_team if val not in no_need_id]


def get_team_id(init_id, no_need_id):
    team_obj = TeamTree()
    id_list = team_obj.filterTeam(init_id,no_need_id)
    return open_list(id_list)


def get_invoice_sum(team_list, year, month):
    all_invoice_obj = MoneyClientModel.objects.filter(team__in=team_list).values('invoice_id')
    time_filter = InvoiceModel.objects.filter(id__in=all_invoice_obj, created__year=year, created__month=month).values(
        'status').annotate(paymentReceived_sum=Sum('paymentReceived'), invoiceAmount_sum=Sum('invoiceAmount'),
                           feeCharge_sum=Sum('feeCharge'))
    print(time_filter)
    print(time_filter.query)
    pass



@timmer
def main(init_id, no_need_id, year, month):
    team_id_list = get_team_id(init_id, no_need_id)
    print('团队id ', len(team_id_list), team_id_list)
    get_invoice_sum(team_id_list, year, month)


top_team_id = 208
no_need_team = []
year = 2023
month = 1
main(top_team_id, no_need_team, year, month)
