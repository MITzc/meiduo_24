from itsdangerous import TimedJSONWebSignatureSerializer as TJWSSerializer, BadData
from django.conf import settings


def generate_save_user_token(openid):
    """ 加密openid """
    # 1. 创建加密序列化对象secret_key
    serializer = TJWSSerializer(settings.SECRET_KEY, 600)

    # 2. 调用dumps(JSON字典)进行加密 加密后的数据默认是bytes 类型
    data = {'openid': openid}
    token = serializer.dump(data)

    # 返回加密后openid
    return token.decode()


def check_save_user_token(access_token):
    """ 传入加密的openid进行解密并返回 """

    # 1. 创建加密的序列化器secret_key
    serializer = TJWSSerializer(settings.SECRET_KEY, 600)

    # 2. 调用loads 方法进行解密
    try:
        data = serializer.loads(access_token)
    except BadData:
        return None
    else:
        return data.get('openid')
