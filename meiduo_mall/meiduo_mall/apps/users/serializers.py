from rest_framework import serializers
# from rest_framework.serializers import Serializer
import re
from django_redis import get_redis_connection
from rest_framework_jwt.settings import api_settings

from .models import User, Address
from celery_tasks.email.tasks import send_verify_email
from goods.models import SKU


class CreateUserSerializer(serializers.ModelSerializer):
    """ 注册序列化器 """
    # 序列化器的所有字段: ['id', 'username', 'password', 'password2', 'mobile', 'sms_code', 'allow']
    # 需要校验的字段: ['username', 'password', 'password2', 'mobile', 'sms_code', 'allow']
    # 模型中已存在的字段: ['id', 'username', 'password', 'mobile']

    # 需要序列化的字段: ['id', 'username', 'mobile', 'token']
    # 需要反序列化的字段: ['username', 'password', 'password2', 'mobile', 'sms_code', 'allow']
    password2 = serializers.CharField(label='确认密码', write_only=True)
    sms_code = serializers.CharField(label='验证码', write_only=True)
    allow = serializers.CharField(label='同意协议', write_only=True)
    token = serializers.CharField(label='token', read_only=True)

    class Mate:
        model = User  # 从User模型中映射序列化字段
        fields = []
        # fields = '__all__'
        fields = ['id', 'username', 'password', 'password2', 'mobile', 'sms_code', 'allow', 'token']
        extra_kwargs = {  # 修改字段选项
            'username': {
                'min_length': 5,
                'max_length': 20,
                'error_messages': {  # 自定义校验出错后的错误信息提示
                    'min_length': '仅允许5-20个字符的用户名',
                    'max_length': '仅允许5-20个字符的用户名',
                }
            },
            'password': {
                'write_only': True,
                'min_length': 8,
                'max_length': 20,
                'error_messages': {
                    'min_length': '仅允许8-20个字符的密码',
                    'max_length': '仅允许8-20个字符的密码',
                }
            }
        }

    def validate_mobile(self, value):
        """ 单独校验手机号码 """
        if not re.match(r'1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号码有误')
        return value

    def validate_allow(self, value):
        """ 是否同意协议 """
        if value != 'true':
            raise serializers.ValidationError('请同意用户协议')
        return value

    def validate(self, attrs):
        """ 校验两个密码是否相同 """
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError('两个秘密不一致')

        # 校验验证码
        redis_conn = get_redis_connection('verify_code')  #####????????
        mobile = attrs['mobile']
        sms_real_code = redis_conn.get('sms_%s' % mobile)
        # 向redis中存储数据都是以字符串形式进行存储,取出来后都是bytes类型  [bytes]
        if sms_real_code is None or attrs['sms_code'] != sms_real_code.decode():
            raise serializers.ValidationError('验证码有误')
        return attrs

    def create(self, validated_data):
        """ 把不需要的password2, sms_code, allow从字段中删除 """
        del validated_data['password2']
        del validated_data['sms_code']
        del validated_data['allow']
        # 把密码先出来
        password = validated_data.pop('password')
        # 创建用户对象,给对象中的username 和 mobile 赋值
        user = User(**validated_data)
        user.set_password(password)  # 把密码赋值后在给user的password 属性
        user.save()  # 存储到数据库

        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER  # 引用jwt中的叫jwt_payload_handler函数(生成payload)
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER  # 函数引用 生成jwt

        payload = jwt_payload_handler(user)  # 根据user生成用户相关的载荷
        token = jwt_encode_handler(payload)  # 传入载荷生成完整的jwt

        user.token = token

        return user


class UserDetailSerializer(serializers.ModelSerializer):
    """用户详情序列化器"""

    class Meta:
        model = User
        fields = ['id', 'username' 'mobile', 'email', 'email_active']


class EmailSerializers(serializers.ModelSerializer):
    """更新邮箱序列化器"""

    class Meta:
        model = User
        fields = ['id', 'email', ]
        extra_kwargs = {
            'email': {
                'required': True
            }
        }

    def update(self, instance, validated_data):
        """ 重写此方法不是为了修改,为了借此时机发送激活邮箱 """
        instance.email = validated_data.get('email')
        instance.save()

        # 将来要在此继续写发邮件的功能
        # send_email()
        # http://www.meiduo.site:8080/success_verify_email.html?token=1
        verify_url = instance.generate_email_verify_url()
        send_verify_email.delay(instance.email, verify_url=verify_url)

        return instance


class UserAddressSerializer(serializers.ModelSerializer):
    """ 用户地址序列化器 """
    province = serializers.StringRelatedField(read_only=True)
    city = serializers.StringRelatedField(read_only=True)
    district = serializers.StringRelatedField(read_only=True)
    province_id = serializers.IntegerField(label='省ID', required=True)
    city_id = serializers.IntegerField(label='市ID', required=True)
    district_id = serializers.IntegerField(label='区ID', required=True)

    class Meta:
        model = Address
        exclude = ('user', 'is_deleted', 'create_time', 'update_time')

    def validate_mobile(self, value):
        """
        验证手机号
        """
        if not re.match(r'^1[3-9]\d{9}$', value):
            raise serializers.ValidationError('手机号格式错误')

        return value

    def create(self, validated_data):
        user = self.context['request'].user  # 获取用户模型对象
        validated_data['user'] = user  # 将用户模型保存到字典中
        return Address.objects.create(**validated_data)


class AddressTitleSerializer(serializers.ModelSerializer):
    """ 地址标题 """

    class Meta:
        model = Address
        fields = ('title',)


class UserBrowserHistorySerializer(serializers.Serializer):
    """ 保存商品浏览记录序列化器 """

    sku_id = serializers.IntegerField(label='商品sku_id', min_value=1)

    def validate_sku_id(self, value):
        """单独对sku_id 进行检验"""
        try:
            SKU.objects.get(id=value)
        except SKU.DoesNotExist:
            return SKU

    def create(self, validated_data):
        sku_id = validated_data.get('sku_id')
        # 获取当前的用户模型对象
        user = self.context['request'].user
        # 创建redis连接对象
        redis_conn = get_redis_connection('history')

        # 创建redis管道
        pl = redis_conn.pipeline()

        # 先去重
        pl.lrem('history_%d' % user.id, 0, sku_id)

        # 再添加到列表的开头
        pl.lpush('history_%d' % user.id, sku_id)

        # 再截取列表中前5个元素
        pl.ltrim('history_%d' % user.id, 0, 4)
        # 执行管道
        pl.execute()

        return validated_data


class SKUSerializer(serializers.ModelSerializer):
    """sku商品序列化器"""

    class Meta:
        model = SKU
        fields = ['id', 'name', 'price', 'default_image_url', 'comments']
