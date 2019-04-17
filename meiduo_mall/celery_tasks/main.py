from celery import Celery
import os

# 告诉celery 如果需要使用django的配置文件因该去哪里加载
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meiduo_mall.settings.dev')

# 创建celery实例例
celery_app = Celery('meiduo')

# 加载celery配置
celery_app.config_from_object('celery_tasks.config')

# ⾃自动注册celery任务
celery_app.autodiscover_tasks(['celery_tasks.sms', 'celery_task.email', 'celery_tasks.html'])
