import base64, pickle
from django_redis import get_redis_connection


def merge_carts_cookie_to_redis(request, user, response):
    """
    登录时合并购物车
    :param request: 登录时借用过来的请求对象
    :param user:    登录时借用过来的用户对象
    :param response:    借用过来准备做删除cookie的响应对对象
    :return:
    """

    # 先获取cookie
    cart_str = request.COOKIE.get('cart')
    # 判断有无cookie购物车数据
    if cart_str is None:
        return

    # 把cookie购物车的字符串转换成字典
    cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))

    # 创建redis连接对象
    redis_conn = get_redis_connection('cart')
    pl = redis_conn.pipeline()

    # 遍历cookie大字典,把sk_id和count向redis的hash存储
    for sku_id in cart_str:
        pl.hset('cart_%d' % user.id, sku_id, cart_dict[sku_id]['count'])
        # 判断当前sk_id是否已经勾选,如果已经勾选就把勾选商品的sku_id存入set集合
        if cart_dict[sku_id]['selected']:
            pl.sadd('selected_%d' % user.id, sku_id)

    pl.execute()

    # 删除cookie购物车数据

    response.delete_cookie('cart')  # 删除cookie
