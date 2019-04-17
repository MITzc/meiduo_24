# 编写异步任务
from celery_tasks.sms.yuntongxun.sms import CCP
from celery_tasks import constants
from celery_tasks.main import celery_app


@celery_app.task(neme='send_sms_code')  # 使用装饰器将send_sms_code装饰为异步任务,并设置别名
def send_sms_code(mobile, sms_code):
    """
     发送短信的异步任务
     mobile:
     sms_code:
     """
    CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60],
                            constants.SEND_SMS_CODE_INTERVAL)
