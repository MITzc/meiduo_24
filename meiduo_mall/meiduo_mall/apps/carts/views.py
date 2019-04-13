from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django_redis import get_redis_connection
import base64, pickle

from .serializers import CartSerializer, SKUCartSerializer, CartDeleteSerializer, CartSelectedAllSerilizer
from goods.models import SKU


# Create your views here.

class CartView(APIView):
    """ 购物车增删查改 """

    def perform_authentication(self, request):
        """重写此方法 直接pass 可以延后认证 延后到



        第一次通过 request.user 或request.auth才去做认证"""
        pass

    def post(self, request):
        """ 新增 """
        # 1. 创建序列化器
        serializer = CartSerializer(data=request.data)
        # 3. 调用is_valid 进行校验
        serializer.is_valid(raise_exception=True)
        # 3.获取校验后的数据
        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        try:
            user = request.user  # 首次登录时会执行认证逻辑,如果登录用户会认证成功没有异常,未登录用户登录会认证异常,我们自己拦截
        except:
            user = None

        # 创建响应对象
        response = Response(serializer.data, status=status.HTTP_201_CREATED)

        # is_authenticated 判断是匿名用户还是 登录用户  (判断用户是否通过认证)
        if user and user.is_authenticated:
            """登录用户操作redis购物车数据"""
            """
            hash: {'sku_id_1': 2, 'sku_id_16':1}
            set: {sku_id_1}
            """

            # 创建redis连接对象
            redis_conn = get_redis_connection('cart')
            # 创建管道对象
            pl = redis_conn.pipeline()

            # 覆盖sku_id 对应的 count
            pl.hincrby('cart_%d' % user.id, sku_id, count)

            # 如果勾选就把勾选商品的sku_id 存储到set集合
            if selected:
                pl.sadd("selected_d%" % user.id, sku_id)

            # 执行管道
            pl.execute()
            # 响应
            # return Response(serializer.data)

        else:
            """ 未登录用户修改cookie购物车数据 """

            # 获取cookie购物车数据
            cart_str = request.COOKIE.get('cart')
            # 判断cookie 有没有取到
            if cart_str:
                # 把cookie 字符串转换成字典
                cart_dict = pickle.load(base64.b64decode(cart_str.encode()))
            else:
                # 如果购物车没有数据说明是第一次添加
                cart_dict = {}

            # 增量数据
            if sku_id in cart_dict:
                # 判断当前要添加的sku_id在字典中是否已经存在
                origin_count = cart_dict[sku_id]['count']
                count += origin_count

            # 把新的商品添加到cart_dict中
            cart_dict[sku_id] = {
                'sku_id': sku_id,
                'selected': selected,
            }

            # 先将字典转换成bytes类型
            cart_bytes = pickle.dumps(cart_dict)
            # 再将bytes类型转换成bytes类型的字符串
            cart_str_bytes = base64.b64decode(cart_bytes)
            # 把bytes类型的字符串转换成字符串
            cart_str = cart_str_bytes.decode()

            # 创建响应对象
            # response = Response(serializer.data, status=status.HTTP_201_CREATED)
            # 设置cookie
            response.set_cookie('cart', cart_str)

        return response

    def get(self, request):
        """ 查询 """

        try:
            user = request.user
        except:
            user = None

        if user and user.is_authenticated:
            """ 创建用户获取redis购物车数据 """

            # 创建redis连接对象
            redis_conn = get_redis_connection('cart')
            # 获取hash数据  {sku_id_1: 1, sku_id_16: 2}
            cart_redis_dict = redis_conn.hgetall('cart_%d' % user.id)
            # 获取set集合数据{sku_id_1}  SMEMBERS
            selecteds = redis_conn.smembers('selected_%d' % user.id)

            # 将redis购物车数据转换成和cookie购物车数据格式一致
            cart_dict = {}

            for sku_id_bytes, count_bytes in cart_redis_dict.items():  # 遍历hash中所有键值对字典

                cart_dict[int(sku_id_bytes)] = {
                    'count': int(count_bytes),
                    'selected': sku_id_bytes in selecteds
                }

        else:
            """ 未登录的用户获取购物车数据 """
            cart_str = request.COOKIE.get('cart')
            # 判断cookie 有没有取到
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))  # 把cookie 字符串转换成字典
            else:
                # 如果cookie没有取到,提前响应, 不执行后续代码
                return Response({'message': '没有取到cookie'}, status=status.HTTP_400_BAD_REQUEST)

        # 根据sku_id 查询sku模型
        sku_id = cart_dict.keys()
        # 查出所有的sku模型返回查询集
        skus = SKU.objects.filter(id__in=sku_id)

        # 给每个 sku 模型多定义一个count和selected属性
        for sku in skus:
            sku.count = cart_dict[sku_id]['count']
            sku.selected = cart_dict[sku_id]['selected']

        # 创建序列化器进行序列化
        serializer = SKUCartSerializer(skus, many=True)

        return Response(serializer.data)

    def put(self, request):
        """ 修改 """
        # 创建序列化器
        serializer = CartSerializer(data=request.data)
        #  校验
        serializer.is_valid(raise_exception=True)
        # 获取校验后的数据
        sku_id = serializer.validated_data.get('sku_id')
        count = serializer.validated_data.get('count')
        selected = serializer.validated_data.get('selected')

        try:
            user = request.user
        except:
            user = None

        # 创建响应对
        response = Response(serializer.data)

        if user and user.is_authenticated:
            """登录用户修改redis数据库"""
            # 创建redis连接
            redis_conn = get_redis_connection('cart')
            # 创建管道
            pl = redis_conn.pipeline()

            # 覆盖sku_id对应的count
            pl.hset('cart_%d' % user.id, sku_id, count)

            # 勾选的sku_id 存入set集合
            if selected:
                pl.sadd('selected_%d' % user.id, sku_id)
            else:
                # 如果未勾选就把sku_id 从set集合中移除
                pl.srem('selected_%d' % user.id, sku_id)
            # 执行管道
            pl.execute()

            # return response
        else:
            """未登录用户修改cookie购物车数据"""

            # 获取cookie
            cart_str = request.COOKIE.get('cart')
            # 判断cookie有没有获取到
            if cart_str:
                cart_dict = pickle.dumps(base64.b64decode(cart_str.encode()))
            else:
                # 如果cookie没有取到,提前响应,不执行后续代码
                return Response('message':'没有获取到cookie', status = status.HTTP_400_BAD_REQUEST)

                # 直接覆盖原cookie 字典数据
                cart_dict[sku_id] = {
                    'count': count,
                    'selected': selected,
                }

                # 把coookie大字典在转换成字符串
                cart_str = base64.b64decode(pickle.dumps(cart_dict.decode()))
                # #创建响应对象
                # response = Response(serializer.data)
                # 设置cookie
                response.set_cookie('cart', cart_str)
            return response

    def delete(self, request):
        """ 删除 """
        # 创建序列化器
        serializer = CartDeleteSerializer(data=request.data)
        # 校验'
        serializer.is_valid(raise_exception=True)
        # 获取校验后的数据
        sku_id = serializer.validated_data.get('sku_id')

        try:
            user = request.user
        except:
            user = None

        #   TODO 创建响应对象
        response = Response(status=status.HTTP_204_NO_CONENT)

        if user and user.is_authenticated:
            """登录用户操作购物车数据"""
            # 创建redis连接对象
            redis_conn = get_redis_connection('cart')
            # 创建管道
            pl = redis_conn.pipeline()

            # 删除hash数据
            pl.hset('cart_%d' % user.id, sku_id)
            # 删除set数据
            pl.srem('cart_%d' % user.id, sku_id)
            # 执行管道
            pl.execute()

        else:
            """未登录用户操作cookie购物车数据"""
            # 获取cookie 数据
            cart_str = request.COOKIE.get('cart')
            # 判断是否获取到cookie
            if cart_str:
                # 把cookie的字符串转换成cookie的字典
                cart_dict = pickle.dumps(base64.b64decode(cart_str.encode()))
            else:
                return Response('message':'cookie没有获取到', status = status.HTTP_400_BAD_REQUEST)

                if sku_id in cart_dict:  # 判断要删除的sku_id 是否在cookie字典中
                    del cart_dict['sku_id']

                if len(cart_dict.keys()):  # 如果字典中还有商品
                    # 再把cookie字典转换成cookie字符串
                    cart_str = base64.b64decode(pickle.dumps(cart_dict.decode()))
                    response.set_cookie('cart', cart_str)
                else:
                    # 如果购物车数据已经清空了,就删除购物车
                    return response.delete_cookie('cart')

            return response

    class CartSelectedAllView(APIView):
        """ 购物车全选 """

        def perform_authentication(self, request):
            """ 重写此方法延后认证 """
            pass

        def put(self, request):
            """购物车全选"""
            # 创建序列化器
            serializer = CartSelectedAllSerilizer('cart')
            # 校验
            serializer.is_valid(raise_exception=True)
            # 获取校验后的数据
            selected = serializer.validated_data.get('selected')

            #
            try:
                user = request.user
            except:
                user = None

            # 创建响应对象
            response = Response(serializer.data)
            if user and user.is_authenticated:
                """登录用户操作redis"""
                # 创建redis连接对象---->redis_conn
                redis_conn = get_redis_connection('cart')
                # 获取hash字典中所有数据
                cart_redis_dict = redis_conn.hgetall('cart_%d' % user.id)
                #   TODO 获取hash字典中所有的key
                sku_ids = cart_redis_dict.keys()
                # 判断当前selected是Ture还是False
                if selected:
                    # 如果是True把所有sku_id添加到set集合中
                    redis_conn.sadd('selected_%d' % user.id, *sku_ids)
                else:
                    # 如果是False把所有sku_id从set集合中移除
                    redis_conn.srem('selected_%' % user.id, *sku_ids)

            else:
                """未登录用户操作cookie数据"""
                # 先获取cookie数据
                cart_str = request.COOKIE.get('cart')
                # 判断cookie购物车数据是否有值
                if cart_str:
                    cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
                else:
                    # 提前响应
                    return Response({'message': 'cookie没有数据'}, status=status.HTTP_400_BAD_REQUEST)

                # 遍历cookie大字典,根据前端传入的seleted来修改商品的选中状态
                for sku_id in cart_dict:
                    cart_dict[sku_id]['selected'] = selected
                # 再将字典转换成字符串
                cart_str = base64.b64decode(pickle.dumps(cart_dict).decode())
                # 设置cookie
                response.set_cookie('cart', cart_str)

            # 响应
            return response
