# coding:utf-8
# @Author:      hk
# @Time:        2022-08-30 17:44:25

from django.db.models import Max
from datetime import datetime, timedelta

from random import randint, uniform
import pandas as pd
from pathlib import Path

from equipments.models import (
    ScadaMsg, ScadaMsgNewest, ScadaAlert, ScadaAlertNewest,
    OnlineMonitorMsg, OnlineMonitorMsgNewest, OnlineMonitorAlert, OnlineMonitorAlertNewest, Code,
    Equipments, InfraredTemperature, InfraredTemperatureNewest
)

from health.models import (
    TrendAssessment, HealthAssessment, HealthAssessmentNewest
)


class Base:
    letter_msg = {}

    def __init__(self):
        self.code_map = {ite.name: ite.uuid for ite in Code.objects.all()}
        self.equ_map = {ite.name: ite.id for ite in Equipments.objects.all()}
        self.now = datetime.now()
        self.equ_id_map = {item.id: {} for item in Equipments.objects.all()}

    def prev_at(self):
        return datetime(self.now.year, self.now.month, self.now.day) - timedelta(days=1)

    def confirm_at(self, model, at: datetime = None):
        """
        历史表数据时间
        历史时间不存在 获取当前时间作为时间
        :param model:
        :param at:
        :return:
        """
        if at:
            return at
        value = model.objects.aggregate(m=Max('at'))
        if value['m']:
            return value['m']
        else:
            return self.prev_at()

    def update_newest(self, equ_map, model1, model2, values, day=7):
        """
        更新最新数据
        :return:
        """
        val = model1.objects.aggregate(m=Max('at'))
        end = val['m']

        start = end - timedelta(days=day)
        for item in model1.objects.filter(at__range=(start, end)).values(*values):
            equ_id = item['equ_id']
            uid = item['field3']
            if equ_map.get(equ_id).get(uid):
                equ_map.get(equ_id).get(uid).append(item)
            else:
                equ_map.get(equ_id)[uid] = [item]

        # 处理 数据
        data = {
            key: [max(item, key=lambda x: x['at']) for _, item in val.items()]
            for key, val in equ_map.items()
        }

        _data = []
        for _equ_id, items in data.items():
            for item in items:
                _data.append(
                    model2(
                        **item
                    )
                )
        model2.objects.bulk_create(_data)

    def letter(self, model, l1, l2, classification=None):
        """
        遥信数据
        告警数据创建，遥信数据复归
        :param model:
        :param l1: 告警状态 tuple
        :param l2: 告警时的状态 目前是唯一一个
        :param classification: 只有 在线监测存在
        :return:
        """
        queryset = model.objects.filter(
            alert_level__in=l1, value1=l2
        ).order_by('at')
        # 告警时间超过一天。 value1 复归 为 0
        data = []
        t_1 = self.now - timedelta(days=1)
        # 筛选告警数据 时间最新数据

        # 告警
        letter_map = {name: {} for name in self.letter_msg.keys()}
        # 消缺告警

        for item in queryset:
            p_name = item.field1
            at = item.at
            equ_id = item.equ_id
            uid = item.field3
            days = (t_1 - at).days
            # 没有消缺告警 告警时间 超过 t-1 天时间 需要消缺
            if item.is_return is False and days >= 1:
                v1 = {
                    'at': at + timedelta(hours=randint(6, 10), minutes=randint(0, 59), seconds=randint(0, 59)),
                    'field1': p_name, 'field3': uid, 'equ_id': equ_id, 'value1': 0,
                    'alert_level': l2, 'is_return': True
                }
                if classification:
                    v1['classification'] = 1
                data.append(model(**v1))
                item.is_return = True
                item.save()
            # 找到数据
            if p_name in letter_map and item.is_return is True:
                letter_map.get(p_name)[at] = (equ_id, uid)

        # 下一个告警数据
        for n_p_name, at_map in letter_map.items():
            if at_map:
                v = max(at_map.keys())
                day = (t_1 - v).days

                if day > self.letter_msg[n_p_name]:
                    e_id, uid = at_map.get(v)
                    v2 = {
                        'at': t_1,
                        'field1': n_p_name, 'field3': uid, 'equ_id': e_id, 'value1': 1,
                        'alert_level': l2,
                    }
                    if classification:
                        v2['classification'] = 1
                    data.append(model(**v2))

        if data:
            model.objects.bulk_create(data)

    def letter_newest(self, m1, m2, special_fields=None):
        """更新 告警数据"""

        data = []
        fields = ['at', 'field1', 'field3', 'equ_id', 'alert_level', 'value1']
        if special_fields:
            fields.extend(special_fields)

        q1 = m1.objects.filter(field1__in=list(self.letter_msg.keys())).values(*fields).order_by('at')
        # 获取每个点位最新数据 取一条
        _map = {item['field3']: item for item in q1}
        for item in _map.values():
            if item['value1'] == 1:
                item['status'] = 1
            data.append(m2(**item))
        m2.objects.filter(field1__in=list(self.letter_msg.keys())).delete()
        m2.objects.bulk_create(data)

    @staticmethod
    def is_create(model, params=None, at_interval=(12, 16)):
        """是否创建"""
        queryset = model.objects.all()
        if params:
            queryset.filter(**params)
        _max = queryset.aggregate(m=Max('at'))
        _at = (datetime.now() - _max['m'] - timedelta(days=1)).days
        return _at >= randint(*at_interval)


class Scada(Base):
    """
    scada 数据分为：遥测（历史、实时）、遥测（历史、实时）
    遥测数据为所有设备 点位每5分钟一个点位
    遥测数据为所有设备告警数据
    """

    # 点位对应时间区间
    letter_msg = {
        '#1主变本体油位异常': 60,
        '温磐2391线开关汇控柜温湿度控制设备故障': 15,
        '温磐2391线开关汇控柜温度异常': 15,
        '温石2392线第一套保护对时异常': 15,
        '磐象1726线保测装置异常': 15
    }

    def __init__(self, day_num=1, point_num=280, ):
        super().__init__()
        self.point_num = point_num
        self.day_num = day_num

    def electric_current(self, current=100):
        """
        电流同加同减
        :return:
        """
        v = (1, -1)[randint(0, 1)]
        current_a = uniform(0, 20) * v
        current_b = uniform(0, 20) * v
        current_c = uniform(0, 20) * v
        a = round(current + current_a, 1)
        b = round(current + current_b, 1)
        c = round(current + current_c, 1)

        return a, b, c

    def scada_1(self):
        """
        温磐2391线GIS
        :return:
        """
        a, b, c = self.electric_current()

        # 电压
        power = round(uniform(123, 131), 2)
        # 因数
        e = round(uniform(0.88, 0.92), 2)
        # 有功
        f = round(3 * (a * power * e) / 1000, 2)
        # 无功
        g = round(f / e - f, 2)
        return f, g, a, b, c, e, power

    def scada_2(self):
        """
        220kV正母GIS
        :return:
        """
        a = round(uniform(123, 131), 2)
        b = round(uniform(123, 131), 2)
        c = round(uniform(123, 131), 2)
        d = round(uniform(215, 225), 2)
        e = round(uniform(3, 11), 2)
        hz = round(uniform(49.99, 50.01), 3)

        return a, b, c, d, e, hz

    def scada_3(self):
        """
        主变
        :return:
        """
        a = round(uniform(35, 45), 1)
        b = round(uniform(35, 45), 1)
        c = round(uniform(35, 45), 1)
        d = 5

        return a, b, c, d

    def scada_4(self):
        """
        #1主变220kV开关GIS
        :return:
        """
        a, b, c = self.electric_current()
        # 因数
        e = round(uniform(0.88, 0.92), 2)
        # 功率
        power = round(a * 220 * 1.732 / 1000, 2)
        # 有功
        f = round(e * power, 2)
        # 无功
        g = round(f / e - f, 2)

        return f, g, a, b, c, e, power

    def scada_5(self):
        """
        #1主变110kV开关GIS
        :return:
        """
        a, b, c = self.electric_current(current=200)
        e = round(uniform(0.88, 0.92), 2)
        # 功率
        power = round(a * 110 * 1.732 / 1000, 2)
        # 有功
        f = round(e * power, 2)
        # 无功
        g = round(f / e - f, 2)

        return f, g, a, b, c, e, power

    def scada_6(self):
        """
        #1主变10kV开关柜
        :return:
        """
        a, b, c = self.electric_current(current=130)
        e = round(uniform(0.88, 0.92), 2)
        # 功率
        power = round(a * 10 * 1.732 / 1000, 2)
        # 有功
        f = round(e * power, 2)
        # 无功
        g = round(f / e - f, 2)

        return f, g, a, b, c, e, power

    def scada_7(self):
        """磐柳1730线GIS"""
        a, b, c = self.electric_current(current=60)
        e = round(uniform(0.88, 0.92), 2)

        # 电压
        voltage = round(uniform(65, 75), 2)

        # 有功
        f = round(3 * (a * e * voltage) / 1000, 2)
        # 无功
        g = round(f / e - f, 2)

        return f, g, a, b, c, e, voltage

    def scada_8(self):
        """
        110kVⅠ段母线GIS
        :return:
        """
        a = round(uniform(55, 65), 2)
        b = round(uniform(55, 65), 2)
        c = round(uniform(55, 65), 2)
        d = round(uniform(55, 65), 2)
        e = round(uniform(1.5, 2.5), 2)
        hz = round(uniform(49.99, 50.01), 3)
        return a, b, c, d, e, hz

    def scada_9(self):
        """
        磐南Y146线开关柜
        :return:
        """
        a, b, c = self.electric_current(current=60)
        e = round(uniform(0.88, 0.92), 2)
        f = round(1.732 * (a * 110 * e) / 1000, 2)
        g = round(f / e - f, 2)
        # return a, b, c, e, f, g
        return f, g, a, b, c, e

    def scada_10(self):
        """
        10kVⅠ段母线压变柜
        :return:
        """
        a = round(uniform(5.6, 5.8), 3)
        b = round(uniform(5.6, 5.8), 3)
        c = round(uniform(5.6, 5.8), 3)
        d = round(uniform(10.7, 10.8), 2)
        e = round(uniform(1, 1.2), 2)
        hz = round(uniform(49.99, 50.01), 3)
        return a, b, c, d, e, hz

    def scada_11(self):
        """
        Ⅱ段母分开关柜
        :return:
        """
        a = 0
        b = 0
        c = 0
        d = 0
        e = 0
        return a, b, c, d, e

    def data_append(self, func, data, points, at, equ_id):
        values = func()
        for index1, (p1, u1) in enumerate(points):
            data.append(
                ScadaMsg(
                    at=at, equ_id=equ_id, field1=p1, field2=u1, value1=values[index1], field3=self.code_map[p1]
                )
            )

    def msg(self):
        """遥测"""
        at = self.confirm_at(ScadaMsg)
        this_path = Path(__file__).parent / 'data.xlsx'
        # 获取 间隔名称 和 遥测点对应关系
        df = pd.read_excel(this_path, sheet_name='Sheet1', keep_default_na=False)
        name_p_map = {ite: [] for ite in set([item for item in df['间隔名称']])}
        for index, row in df.iterrows():
            name_p_map.get(row['间隔名称']).append((row['遥测信息'], row['单位']))

        # 增加不存在 excel 表中的间隔
        # 温磐2391线GIS
        name1 = name_p_map.pop('温磐2391线GIS')
        names_1 = """
                   磐楠24U1线
                   温石2392线
                   磐江24U2线
                   温磐2391线
               """.strip().split()
        for ite in names_1:
            # 间隔名称
            name_p_map['%sGIS' % ite] = [('%s%s' % (ite, m), u) for m, u in name1]
        # 磐柳1730线GIS
        name2 = name_p_map.pop('磐柳1730线GIS')
        names_2 = """
                   磐象1726线
                   万磐1306线
                   磐里1728线
                   磐柳1730线
               """.strip().split()
        for ite in names_2:
            # 间隔名称
            name_p_map['%sGIS' % ite] = [('%s%s' % (ite, m), u) for m, u in name2]

        # 磐南Y146线开关柜
        name3 = name_p_map.pop('磐南Y146线开关柜')
        names_3 = """
                   磐南Y146线
                   西街Y147线
                   佳利Y148线
                   待用Y149线
                   待用Y150线
                   待用Y151线
                   待用Y152线
                   待用Y153线
                   磐东Y185线
                   磐西Y186线
                   河北Y187线
                   象石Y188线
                   油车Y189线
                   待用Y190线
                   待用Y191线
                   待用Y192线
                   #1电容器
                   #2电容器
                   #3电容器
                   #4电容器
                   #5电容器
                   #6电容器
                   #1接地变
                   #2接地变
               """.strip().split()
        for ite in names_3:
            # 间隔名称
            name_p_map['%s开关柜' % ite] = [('%s%s' % (ite, m), u) for m, u in name3]
        data = []
        at = datetime(at.year, at.month, at.day) + timedelta(days=1)
        # 每天 280 个 点
        for j in range(self.point_num):
            day = at + timedelta(minutes=5 * j, seconds=randint(0, 59))
            for equ_name, points in name_p_map.items():
                equ_id = self.equ_map[equ_name]
                # 创建数据
                if len(data) > 5000:
                    ScadaMsg.objects.bulk_create(data)
                    data.clear()
                # 间隔 样式一
                if equ_name in ['%sGIS' % item for item in names_1]:
                    func = self.scada_1
                # 间隔 样式二
                elif equ_name in ('220kV正母GIS', '220kV副母GIS'):
                    func = self.scada_2
                # 间隔 样式三
                elif equ_name in ('#1主变', '#2主变'):
                    func = self.scada_3
                # 间隔 样式四
                elif equ_name in ('#1主变220kV开关GIS', '#2主变220kV开关GIS'):
                    func = self.scada_4
                # 间隔 样式五
                elif equ_name in ('#1主变110kV开关GIS', '#2主变110kV开关GIS'):
                    func = self.scada_5
                # 间隔 样式六
                elif equ_name in ('#1主变10kV开关柜', '#2主变10kV开关柜'):
                    func = self.scada_6
                elif equ_name in ['%sGIS' % item for item in names_2]:
                    func = self.scada_7
                elif equ_name in ('110kVⅠ段母线GIS', '110kVⅡ段母线GIS'):
                    func = self.scada_8
                elif equ_name in ['%s开关柜' % item for item in names_3]:
                    func = self.scada_9
                elif equ_name in ('10kVⅠ段母线压变柜', '10kVⅡ段母线压变柜'):
                    func = self.scada_10
                elif equ_name in ('10kVⅠ-Ⅱ段母分开关柜', '110kVⅠ-Ⅱ段母分开关GIS', '220kV母联开关GIS'):
                    func = self.scada_11
                else:
                    continue
                # 处理数据
                self.data_append(
                    func=func, data=data, points=points, at=day, equ_id=equ_id
                )
        if data:
            ScadaMsg.objects.bulk_create(data)

    def msg_newest(self):
        """更新最新数据"""
        ScadaMsgNewest.objects.all().delete()
        values = ('at', 'equ_id', 'field1', 'field3', 'value1', 'field2')
        equ_map = {item['equ_id']: {} for item in ScadaMsg.objects.distinct().values('equ_id')}
        self.update_newest(equ_map, ScadaMsg, ScadaMsgNewest, values)


class OnlineMonitor(Base):
    """
    在线监测 数据分为：遥测（历史、实时）、遥测（历史、实时）
    1. 油色谱数据 两个小时一个点位
    2. 电流为 半小时一个点位
    3. sf 气体压力为 两个周一个点位
    遥测数据为所有设备告警数据
    """

    letter_msg = {
        '温磐2391线开关SF6气压低告警': 30, '总烃产气速率大于10%/月': 30
    }

    def __init__(self, at=None, day_num=1):
        super().__init__()
        self.day_num = day_num
        self.at = at

    def get_gas_val(self):
        """
        气体值
        H2
        CH4
        C2H4
        C2H6
        C2H2
        CO
        CO2
        O2
        N2
        MST
        总可燃气体
        总气体

        变压器独有
        :return:
        """
        a = round(uniform(1, 5), 4)
        b = round(uniform(0, 5), 4)
        c = round(uniform(1, 5), 4)
        d = round(uniform(0, 5), 4)
        e = round(uniform(0, 5), 4)
        f = round(uniform(5, 10), 4)
        g = round(uniform(10, 20), 4)
        h = round(uniform(0, 5), 4)
        i = round(uniform(0, 5), 4)
        j = round(uniform(0, 5), 4)

        total = round(
            a + b + c + d + e, 4
        )
        _total = round(
            a + b + c + d + e + f + g + h + i, 4
        )

        return a, b, c, d, e, f, g, h, i, j, total, _total

    def current_val(self):
        """
        电流
        变压器独有
        :return:
        """
        a = round(uniform(4.7, 5.3), 2)
        b = round(uniform(1.7, 2.3), 2)
        return a, b

    def oil_gas(self, at):
        """
        油中溶解气体
        两个小时一个点位
        :return:
        """

        val = """
           H2
           CH4
           C2H4
           C2H6
           C2H2
           CO
           CO2
           O2
           N2
           MST
           总可燃气体
           总气体
           """.strip().split()
        data = []
        # 气体 每两小时一个点
        for j in range(12):
            day = at + timedelta(hours=2 * j, minutes=randint(1, 10), seconds=randint(0, 59))
            for equ_id in (107, 108):
                for gas_index, gas_val in enumerate(self.get_gas_val()):
                    data.append(
                        OnlineMonitorMsg(
                            at=day,
                            field1=val[gas_index],
                            field2='µL/L',
                            field3=self.code_map[val[gas_index]],
                            value1=gas_val,
                            classification=1,
                            equ_id=equ_id
                        )
                    )
        OnlineMonitorMsg.objects.bulk_create(data)

    def current(self, at):
        """
        电流
        半个小时一个点位
        :return:
        """

        val = """
           夹件接地电流
           铁芯接地电流
           """.strip().split()

        data = []
        for i in range(48):
            day = at + timedelta(minutes=30 * i, seconds=randint(1, 60))
            for equ_id in (107, 108):
                for current_index, cur in enumerate(self.current_val()):
                    classification = 5 if not current_index else 2
                    data.append(
                        OnlineMonitorMsg(
                            at=day,
                            field1=val[current_index],
                            field2='mA',
                            field3=self.code_map[val[current_index]],
                            value1=cur,
                            classification=classification,
                            equ_id=equ_id
                        )
                    )

        OnlineMonitorMsg.objects.bulk_create(data)

    def sf6(self, at):
        """
        sf 气体密度
        :return:
        """
        # 14 天一个点位
        # 判断是否需要创建
        if self.is_create(OnlineMonitorMsg, {'classification': 3}):
            n1 = """
                温石2392
                磐楠24U1
                磐江24U2
                温磐2391
                """.strip().split()
            n2 = """
                磐象1726
                万盘1306
                磐里1728
                磐柳1730
                """.strip().split()
            this_path = Path(__file__).parent / 'data.xlsx'
            df = pd.read_excel(this_path, sheet_name='Sheet3', keep_default_na=False)

            equ_point_map = {item: [] for item in set(df['间隔名称'])}
            for index, row in df.iterrows():
                equ_point_map.get(row['间隔名称']).append((row['遥测信息'], row['数值']))

            n1_values = equ_point_map.pop('温石2392线GIS')
            n2_values = equ_point_map.pop('磐柳1730线GIS')
            equ_uuid_map = {self.equ_map[key]: val for key, val in equ_point_map.items()}

            # 处理 相同值 不同 间隔问题
            for item1 in n1:
                equ_id = self.equ_map['%s线GIS' % item1]
                equ_uuid_map[equ_id] = [
                    (
                        '%s%s' % (item1, m), val
                    )
                    for m, val in n1_values
                ]
            for item2 in n2:
                equ_id = self.equ_map['%s线GIS' % item2]
                equ_uuid_map[equ_id] = [
                    (
                        '%s%s' % (item2, m), val
                    )
                    for m, val in n2_values
                ]

            data = []
            day = at + timedelta(hours=randint(10, 18), minutes=randint(0, 59), seconds=randint(0, 59))
            for equ_id, points in equ_uuid_map.items():
                for msg, val in points:
                    data.append(
                        OnlineMonitorMsg(
                            at=day,
                            field1=msg,
                            field2='MPa',
                            field3=self.code_map[msg],
                            value1=round(0.6 + uniform(-0.03, 0.03), 4),
                            classification=3,
                            equ_id=equ_id
                        )
                    )

            OnlineMonitorMsg.objects.bulk_create(data)

    def msg(self):
        """生成"""
        at = self.at if self.at else self.prev_at()
        self.oil_gas(at)
        self.current(at)
        self.sf6(at)

    def msg_newest(self):
        """
        更新 实时表
        :return:
        """
        OnlineMonitorMsgNewest.objects.all().delete()
        values = ('at', 'field1', 'field2', 'field3', 'value1', 'classification', 'equ_id')
        equ_map = {item.id: {} for item in Equipments.objects.filter(classification__in=(0, 1))}
        self.update_newest(equ_map, OnlineMonitorMsg, OnlineMonitorMsgNewest, values, 17)


class Infrared(Base):
    """
    在线监测 数据分为：遥测（历史、实时）
    两个周一个点位
    """

    @staticmethod
    def temperature(at):
        """
        处理温度
        :return:
        """
        hour = at.hour
        if 11 <= hour <= 16:
            return uniform(20, 40)
        elif 9 <= hour < 10:
            return uniform(15, 25)
        elif 16 < hour <= 18:
            return uniform(25, 35)
        else:
            return uniform(15, 20)

    def msg(self):
        """
        生成 数据
        :return:
        """
        # 判断是否需要生成数据
        if self.is_create(InfraredTemperature, ):
            this_path = Path(__file__).parent / 'data.xlsx'
            df = pd.read_excel(this_path, sheet_name='Sheet3', keep_default_na=False)

            equ_point_map = {item.strip(): [] for item in set(df['间隔名称'])}

            for index, row in df.iterrows():
                equ_point_map[row['间隔名称'].strip()].append(row['遥测信息'])

            n1 = """
                   温石2392
                   磐楠24U1
                   磐江24U2
                   温磐2391
               """.strip().split()

            n2 = """
                   磐柳1730
                   磐象1726
                   万盘1306
                   磐里1728
                   """.strip().split()

            n3 = """
                   西街Y147线开关柜
                   #1主变10kV开关柜
                   #1主变10kV隔离柜
                   #2主变10kV开关柜
                   #2主变10kV隔离柜
                   磐南Y146线开关柜
                   佳利Y148线开关柜
                   待用Y149线开关柜
                   待用Y150线开关柜
                   待用Y151线开关柜
                   待用Y152线开关柜
                   待用Y153线开关柜
                   磐东Y185线开关柜
                   磐西Y186线开关柜
                   河北Y187线开关柜
                   象石Y188线开关柜
                   油车Y189线开关柜
                   待用Y190线开关柜
                   待用Y191线开关柜
                   待用Y192线开关柜
                   10kVⅠ段母线压变柜
                   10kVⅡ段母线压变柜
                   10kVⅠ-Ⅱ段母分隔离柜
                   10kVⅠ-Ⅱ段母分开关柜
                   #1电容器开关柜
                   #2电容器开关柜
                   #3电容器开关柜
                   #4电容器开关柜
                   #5电容器开关柜
                   #6电容器开关柜
                   #1接地变开关柜
                   #2接地变开关柜
                   """.strip().split()

            n5 = """
                   西街Y147
                   #1主变10kV
                   #1主变10kV
                   #2主变10kV
                   #2主变10kV
                   磐南Y146线
                   佳利Y148线
                   待用Y149线
                   待用Y150线
                   待用Y151线
                   待用Y152线
                   待用Y153线
                   磐东Y185线
                   磐西Y186线
                   河北Y187线
                   象石Y188线
                   油车Y189线
                   待用Y190线
                   待用Y191线
                   待用Y192线
                   10kVⅠ段母线
                   10kVⅡ段母线
                   10kVⅠ-Ⅱ段母分
                   10kVⅠ-Ⅱ段母分
                   #1电容器
                   #2电容器
                   #3电容器
                   #4电容器
                   #5电容器
                   #6电容器
                   #1接地变
                   #2接地变
               """.strip().split()

            n1_values = equ_point_map.pop('温磐2391线GIS')
            n2_values = equ_point_map.pop('磐柳1730线GIS')
            n3_values = equ_point_map.pop('西街Y147线开关柜')

            for item1 in n1:
                equ_point_map['%s线GIS' % item1] = [
                    '%s%s' % (item1, item)
                    for item in n1_values
                ]
            for item2 in n2:
                equ_point_map['%s线GIS' % item2] = [
                    '%s%s' % (item2, item)
                    for item in n2_values
                ]

            for _index, item in enumerate(n3):
                equ_point_map[item] = [
                    '%s%s' % (n5[_index], ite)
                    for ite in n3_values
                ]

            # 名称 更换为 id
            equ_point_map = {self.equ_map[key]: val for key, val in equ_point_map.items()}
            data = []

            at = self.prev_at()
            day = at + timedelta(hours=randint(9, 18), minutes=randint(0, 59), seconds=randint(0, 59))
            for equ_id, points in equ_point_map.items():
                for point in points:
                    data.append(
                        InfraredTemperature(
                            at=day,
                            field1=point,
                            field2='℃',
                            field3=self.code_map[point],
                            value1=round(self.temperature(day), 2),
                            equ_id=equ_id
                        )
                    )
            InfraredTemperature.objects.bulk_create(data)

    def msg_newest(self):
        """实时数据"""
        # 是否更新

        InfraredTemperatureNewest.objects.all().delete()
        values = ('at', 'field1', 'field2', 'field3', 'value1', 'equ_id')
        equ_map = {item: {} for item in self.equ_id_map.keys()}
        self.update_newest(equ_map, InfraredTemperature, InfraredTemperatureNewest, values, 17)


class Assessment(Base):
    """
    设备健康评估
    """
    score_map = {
        '#1主变本体油位异常': -8, '温磐2391线开关汇控柜温湿度控制设备故障': -2,
        '温磐2391线开关汇控柜温度异常': -2, '温石2392线第一套保护对时异常': -2,
        '磐象1726线保测装置异常': -2,
        '温磐2391线开关SF6气压低告警': -10, '烃产气速率大于10%/月': -10
    }

    def msg_newest(self):
        """更新实时表"""
        at = self.prev_at()
        # scada 告警
        end_at = datetime(at.year, at.month, at.day, 23, 59, 59)
        q1 = ScadaAlertNewest.objects.filter(alert_level__in=(0, 1, 2), value1=1).values('field1', 'equ_id')
        # 在线监测告警
        q2 = OnlineMonitorAlertNewest.objects.filter(value1=1, at__range=(at, end_at)).values('field1', 'equ_id')

        q1_map = {item['equ_id']: item['field1'] for item in q1}
        q2_map = {item['equ_id']: item['field1'] for item in q2}

        # 生成设备健康分组
        data = []
        _data = []
        for equ_id in self.equ_map.values():
            base_score = 100
            v1 = q1_map.get(equ_id)
            v2 = q2_map.get(equ_id)

            if v1 and self.score_map.get(v1):
                electrical_score = self.score_map[v1]
            else:
                electrical_score = 0

            if v2 and self.score_map.get(v2):
                defect_score = self.score_map[v2]
            else:
                defect_score = 0
            total_score = base_score + (defect_score + electrical_score)

            val = {
                'at': at,
                'equ_id': equ_id,
                'total_score': total_score,
                'base_score': base_score,
                'defect_score': defect_score,
                'electrical_score': electrical_score,
                'trend_score': 0,
                'conclusion': '设备正常',
                'status': 0
            }
            data.append(HealthAssessment(**val))
            _data.append(HealthAssessmentNewest(**val))
        HealthAssessmentNewest.objects.all().delete()
        HealthAssessment.objects.bulk_create(data)
        HealthAssessmentNewest.objects.bulk_create(_data)


class Trend(Base):
    """
    设备趋势评估分析 只是更新 获取图表的时间即可
    """

    def update_at(self):
        at = self.prev_at()
        end_at = datetime(
            at.year, at.month, at.day, hour=randint(8, 18), minute=randint(0, 59), second=randint(0, 59)
        )
        start_at = end_at - timedelta(days=1)
        TrendAssessment.objects.update(start_at=start_at, end_at=end_at)
