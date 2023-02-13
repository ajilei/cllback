# coding:utf-8
# @Author:      kai
# @Time:        2022-05-30 22:21:24
import os
from celery import Celery, platforms
from async_tasks import config

# platforms.C_FORCE_ROOT = True

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangoProject2.settings")  # 引用django的环境
celery_app = Celery('app')  # 创建 celery 实例
celery_app.config_from_object(config)  # 加载配置
# 加载 tasks

celery_app.autodiscover_tasks([
    'async_tasks.archive'
])
