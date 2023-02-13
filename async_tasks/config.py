# coding:utf-8
# @Author:      kai
# @Time:        2022-05-30 22:21:38

from async_tasks.schedules_config import beat_schedules

broker_url = f'redis://localhost:6379/2'

# 配置celery时区，默认时UTC。
timezone = 'Asia/Shanghai'
# 可接受的内容格式
accept_content = ['pickle', 'json']
# 任务序列化数据格式
task_serializer = "json"
# 结果序列化数据格式
result_serializer = "json"

result_backend = f'redis://localhost:6379/1'
result_cache_max = 100  # 任务结果最大缓存数量
result_expires = 3600  # 任务过期时间

worker_redirect_stdouts_level = 'INFO'

# 可选参数：给某个任务限流
# task_annotations = {'tasks.my_task': {'rate_limit': '10/s'}}

# 可选参数：给任务设置超时时间。超时立即中止worker
# task_time_limit = 10 * 60

# 可选参数：给任务设置软超时时间，超时抛出Exception
# task_soft_time_limit = 10 * 60

# 可选参数：如果使用django_celery_beat进行定时任务
# beat_scheduler = "django_celery_beat.schedulers:DatabaseScheduler"

# set default false, use celery logging config in django setting.py
# worker_hijack_root_logger = True

beat_schedule_filename = 'celery-beat'

imports = [
]

beat_schedule = beat_schedules
