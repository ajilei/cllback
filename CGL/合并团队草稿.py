import pandas as pd
import numpy as np


def update_user_name(file_path):
    a_dict = {}
    execpt_re = []
    raw_data = pd.read_excel(file_path, header=0)  # header=0表示第一行是表头，就自动去除了
    for i in raw_data.values:
        if i[1] and not type(i[1]) == float:
            try:
                re_str = i[1].split(' - ')
            except Exception as e:
                execpt_re.append(list(i))
                continue
            if len(re_str) > 1:
                group_name, user_name = re_str[0], re_str[1]
                if user_name not in a_dict:
                    a_dict[user_name] = []
                try:
                    a_dict[user_name].append(list(i))
                except Exception as e:
                    print(e)
        else:
            execpt_re.append(i[0])

    print('团队名称：', execpt_re, '匹配不到 - 字符，或不存在一级团队跳过，需要自己检查')
    print(a_dict)


def main():
    file_path = r'/Users/leiji/Downloads/2023-02-02-一级团队业绩分析 (1).xlsx'
    update_user_name(file_path)


if __name__ == '__main__':
    main()
