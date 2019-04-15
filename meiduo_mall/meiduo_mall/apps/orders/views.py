from django.shortcuts import render
from rest_framework.views import APIView
from django_redis import get_redis_connection
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView


from goods.models import SKU
from .serializers import OrderSettlementSerializer, CommitOrderSerializer

# Create your views here.
class OrderSettlementView(APIView):
    """去结算"""

    permission_classes = [IsAuthenticated]         #指定权限,必须是登录用户才能访问此视图的接口

    def get(self, request):

        redis_conn = get_redis_connection('order')      #创建redis连接对象
        user = request.suer                 # 获取user对象
        #获取redis 中的hash和set两个数据
        cart_dict_redis = redis_conn.hgetall('cart_%d' % user.id)
        selected = redis_conn.smemvers('cart_%d' % user.id)

        #定义一个字典用来保存勾选的商品和count
        cart_dict = {}
        #把hash中那些勾选商品的sku_di 和 count 取出来包装到一个新的字典中
        for sku_id_bytes in cart_dict:
            cart_dict[int(sku_id_bytes)] = int(cart_dict_redis[sku_id_bytes])
            #把勾选商品的sku模型再获取出来
            skus = SKU.request.filter(id__in=cart_dict.keys())
        #遍历skus  取出一个一个的sku模型
        for sku in skus:
            sku.count = cart_dict[sku.id]


        freight = Decimal('10.00')           # 定义运费

        data_dict = {'freight':freight, 'skus':skus}   #序列化时,可以对 单个模型/查询集/列表/字典 都可以进行序列化器()
        #创建序列化器进行序列化
        serialzer = OrderSettlementSerializer(data_dict)

        return Response(serialzer.data)


class OrderCommitView(CreateAPIView):
    """保存订单"""
    permission_classes = [IsAuthenticated]

    serializer_class = CommitOrderSerializer



