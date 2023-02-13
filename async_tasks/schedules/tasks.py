# coding=utf-8
import os
import copy as cp
import pandas as pd
import datetime
import re as ree

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject2.settings')

import django

django.setup()

from django.db.models import Sum, Q
from django.core.mail import EmailMessage

from TEAM.models import TeamModel
from INVOICE.models import InvoiceModel
from INVOICE.models import MoneyClientModel
from USER.models import UserModel

from tool.decorator_tool import timmer
from async_tasks import celery_app as app

# 写的最垃圾的代码，毁灭吧！！！！

class get_money(object):
    @staticmethod
    def one_team(start, end):
        one_team = TeamModel.objects.filter(parent_id=1).exclude(
            Q(name__icontains='离职') | Q(name__icontains='总经理办公室') | Q(name__icontains='CGL数智化') | Q(
                name__icontains='Z-SSC') | Q(name__icontains='MCG团队') | Q(name__icontains='全国洛依') | Q(
                name__icontains='广州一分 - 500'))
        two_team = TeamModel.objects.filter(parent__in=one_team).exclude(name__contains='独立')
        res_dict = {}
        count = 0
        for i in two_team:
            # 三人不成团
            vv = UserModel.objects.filter(team=i, status='Active')
            num = vv.count()
            all_invoice_obj = MoneyClientModel.objects.filter(user__team=i).values('invoice')
            Q1 = Q(id__in=all_invoice_obj, active='1')
            Q4 = Q(created__gt=start, created__lt=end)
            # billing
            billing_filter = InvoiceModel.objects.filter(Q1 & Q4).exclude(status='Reject')
            billing = MoneyClientModel.objects.filter(invoice__in=billing_filter, user__team=i).values(
                'user__team').annotate(
                Sum('revenue'))
            # 开票金额
            Q2 = Q(status__in=['Received', 'Sent'], time2__gt=start, time2__lt=end)
            invoice_filter = InvoiceModel.objects.filter(Q1 & Q2)
            invoice = MoneyClientModel.objects.filter(invoice__in=invoice_filter, user__team=i).values(
                'user__team').annotate(
                Sum('revenue'))

            # 到款金额
            Q3 = Q(status__in=['Received'], time3__gt=start, time3__lt=end)
            send_filter = InvoiceModel.objects.filter(Q1 & Q3)
            send = MoneyClientModel.objects.filter(invoice__in=send_filter, user__team=i).values('user__team').annotate(
                Sum('revenue'))
            billing_sum = billing[0]['revenue__sum'] if billing.count() else 0
            invoice_sum = invoice[0]['revenue__sum'] if invoice.count() else 0
            send_sum = send[0]['revenue__sum'] if send.count() else 0
            re = i.name.split('-')
            if len(re) > 2:
                index = re[2].strip()
            else:
                index = '0万'
            if len(re) > 1:
                name = re[1].strip()
                dd = re[0].strip()
            # 处理二级团队
            if i.children.exists():
                for j in i.children.all():
                    if name == 'Gin Ren':
                        print(1)
                    num += UserModel.objects.filter(team=j, status='Active').count()
                    all_invoice_obj_2 = MoneyClientModel.objects.filter(user__team=j).values('invoice')
                    Q1 = Q(id__in=all_invoice_obj_2, active='1')
                    billing_filter_2 = InvoiceModel.objects.filter(Q1 & Q4).exclude(status='Reject')
                    billing_2 = MoneyClientModel.objects.filter(invoice__in=billing_filter_2, user__team=j).values(
                        'user__team').annotate(
                        Sum('revenue'))
                    # 开票金额
                    Q2 = Q(status__in=['Received', 'Sent'], time2__gt=start, time2__lt=end)
                    invoice_filter_2 = InvoiceModel.objects.filter(Q1 & Q2)
                    invoice_2 = MoneyClientModel.objects.filter(invoice__in=invoice_filter_2, user__team=j).values(
                        'user__team').annotate(
                        Sum('revenue'))

                    # 到款金额
                    Q3 = Q(status__in=['Received'], time3__gt=start, time3__lt=end)
                    send_filter_2 = InvoiceModel.objects.filter(Q1 & Q3)
                    send_2 = MoneyClientModel.objects.filter(invoice__in=send_filter_2, user__team=j).values(
                        'user__team').annotate(
                        Sum('revenue'))
                    billing_sum += billing_2[0]['revenue__sum'] if billing_2.count() else 0
                    invoice_sum += invoice_2[0]['revenue__sum'] if invoice_2.count() else 0
                    send_sum += send_2[0]['revenue__sum'] if send_2.count() else 0

                    # 处理三级团队
                    if j.children.exists():
                        for q in j.children.all():
                            num += UserModel.objects.filter(team=q, status='Active').count()
                            all_invoice_obj_3 = MoneyClientModel.objects.filter(user__team=q).values('invoice')
                            Q1 = Q(id__in=all_invoice_obj_3, active='1')
                            billing_filter_3 = InvoiceModel.objects.filter(Q1 & Q4).exclude(status='Reject')
                            billing_3 = MoneyClientModel.objects.filter(invoice__in=billing_filter_3,
                                                                        user__team=q).values(
                                'user__team').annotate(
                                Sum('revenue'))
                            # 开票金额
                            Q2 = Q(status__in=['Received', 'Sent'], time2__gt=start, time2__lt=end)
                            invoice_filter_3 = InvoiceModel.objects.filter(Q1 & Q2)
                            invoice_3 = MoneyClientModel.objects.filter(invoice__in=invoice_filter_3,
                                                                        user__team=q).values('user__team').annotate(
                                Sum('revenue'))

                            # 到款金额
                            Q3 = Q(status__in=['Received'], time3__gt=start, time3__lt=end)
                            send_filter_3 = InvoiceModel.objects.filter(Q1 & Q3)
                            send_3 = MoneyClientModel.objects.filter(invoice__in=send_filter_3, user__team=q).values(
                                'user__team').annotate(
                                Sum('revenue'))
                            billing_sum += billing_3[0]['revenue__sum'] if billing_3.count() else 0
                            invoice_sum += invoice_3[0]['revenue__sum'] if invoice_3.count() else 0
                            send_sum += send_3[0]['revenue__sum'] if send_3.count() else 0
            res_go_out_user = {}
            if num < 3:
                if TeamModel.objects.filter(name__icontains=name, parent__in=one_team).count() < 2:
                    continue
            if 'Caroline Xiao' in name or 'Harry WU' in name or 'Jason Xuan' in name:
                continue
            email = ''
            if name == 'Chris Yang':
                cc = name
                name = 'Chris Yang - SU'
            if name == 'Catherine Meiji Tantai':
                ccc = name
                name = 'Catherine MEIJI'
            if UserModel.objects.filter(name=name).exists():
                email = UserModel.objects.filter(name=name).values('email')[0]['email']
            if UserModel.objects.filter(name=name,leaveDate__lt=start).exists():
                continue
            if name == 'Catherine Meiji Tantai':
                name = ccc
            res_dict[i.id] = {'id': i.id, 'name': i.name, 'billing': billing_sum, 'invoice': invoice_sum,
                              'send': send_sum, 'leader': name, 'index': index, 'email': email, 'dd': dd}
            res_go_out_user[i.id] = {'id': i.id, 'name': i.name, 'billing': billing_sum, 'invoice': invoice_sum,
                                     'send': send_sum, 'leader': name, 'index': index, 'email': email, 'dd': dd}

        print(res_go_out_user)
        print(res_dict)
        return res_dict, res_go_out_user


# 团队id，用户id
def make_dict(ing, go_out):
    copy = cp.deepcopy(ing)
    dictX = {}
    for i in copy:
        for j in copy:
            if copy[i]['leader'] == copy[j]['leader'] and not i == j:
                if i in dictX:
                    c = dictX[i]
                    c.append(j)
                    dictX[i] = c
                else:
                    dictX[i] = [i, j]

    for i in dictX:
        if not i in ing:
            continue
        name = copy[i]['dd'].split('团队')[0] + '团队'
        listA = [None, name, 0, 0, 0, 0, '']
        new_key = str(i)
        for j in dictX[i]:
            new_key = new_key + '-' + str(j)
            listA[0] = new_key
            listA[2] = listA[2] + ing[j]['billing']
            listA[3] = listA[3] + ing[j]['invoice']
            listA[4] = listA[4] + ing[j]['send']
            # listA[5] = listA[5] + ing[j]['index']
            listA[5] = listA[5] + float(ing[j]['index'].split('万')[0])
            listA[6] = str(listA[5]) + '万'
            ing.pop(j)
        ing[new_key] = {'name': name, 'billing': listA[2], 'invoice': listA[3], 'send': listA[4], 'index': listA[6],
                        'leader': copy[j]['leader'], 'email': copy[j]['email']}
    return ing


def go_execl(ing, start):
    month = 1
    result = []
    title = [['团队名称', 'Billing业绩', '开票金额', '到账金额', '全年指标', str(month) + '月指标', '开票完成率排名',
              '开票排名',
              'billing业绩排名',
              '到账金额排名',
              '开票完成率', '负责人', '邮箱']]
    for i in ing:
        index = 0
        all_index = float(ing[i]['index'].split('万')[0])
        all_index = int(all_index * 10000)
        if month in [1, 2, 3, 10, 11, 12]:
            index = round(all_index / 15, 2)
        elif month in [4, 5, 6, 7, 8, 9]:
            index = all_index / 10
        c = index / 100
        if not c == 0:
            d = str(round(ing[i]['invoice'] / c, 2)) + '%'
        else:
            d = "0%"
        result.append([ing[i]['name'].split('-')[0], ing[i]['billing'], ing[i]['invoice'], ing[i]['send'],
                       all_index,
                       index, None, None,
                       None, None
                          , d, ing[i]['leader'], ing[i]['email']])

    b = list(enumerate(result))

    # 开票排名
    c = sorted(b, key=lambda x: -x[1][2])
    count = 1
    for i in c:
        result[i[0]][7] = count
        count += 1
    # 开票完成率排名
    c = sorted(b, key=lambda x: -float(x[1][10].split('%')[0]))
    count = 1
    for i in c:
        result[i[0]][6] = count
        count += 1

    # billing排名
    c = sorted(b, key=lambda x: -x[1][1])
    count = 1
    for i in c:
        result[i[0]][8] = count
        count += 1

    # 到账金额排名
    c = sorted(b, key=lambda x: -x[1][3])
    count = 1
    for i in c:
        result[i[0]][9] = count
        count += 1

    title.extend(result)
    df = pd.DataFrame(title)
    now = str(datetime.datetime.now())
    name = '一级团队业绩' + now + '.xlsx'
    dd=ree.sub(r' ','-',name)
    df.to_excel(name, index=False, header=None)
    return name


@app.task()
def onteamupdate(start, end, email):
    ing, go_out = get_money.one_team(start, end)
    ing = make_dict(ing, go_out)
    name = go_execl(ing, start)
    email = EmailMessage(
        name.split('.xlsx')[0],
        name.split('.xlsx')[0],
        '3467466810@qq.com',
        [email],
        [email],
        headers={'Message-ID': 'foo'},
    )
    email.attach_file(name)
    email.send()
