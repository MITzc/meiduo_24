from django.shortcuts import render
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView, CreateAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.mixins import UpdateModelMixin
from rest_framework.viewsets import GenericViewSet
from django_redis import get_redis_connection
from rest_framework_jwt.views import ObtainJSONWebToken
from rest_framework_jwt.settings import api_settings



from .models import User, Address
from .serializers import UserDetailSerializer, EmailSerializers, UserAddressSerializer, UserBrowserHistorySerializer,CreateUserSerializer, AddressTitleSerializer




# Create your views here.


class UserView(CreateAPIView):
    """ 用户注册"""
    # 指定序列化器
    serializer_class = CreateUserSerializer


class UsernameCountView(APIView):
    """ 判断用户是否已经注册 """

    def get(self, request, username):
        # 查询user 表
        count = User.objects.filter(username=username).count()
        # 包装响应数据
        data = {
            "username": username,
            "count": count
        }

        return Response(data)


class MobileCountView(APIView):
    """ 判断手机号码是否已经注册 """

    def get(self, request, mobile):
        count = User.objects.filter(mobile=mobile).count()

        data = {
            "mobile": mobile,
            "count": count
        }

        # 响应
        return Response(data)


# GET /user
class UserDetailView(RetrieveAPIView):
    """ 用户详情展示 """
    serializer_class = UserDetailSerializer  # 指定序列化器

    permission_classes = [IsAuthenticated]  # 指定权限.只有通过认证的用户才能访问当前视图

    def get_object(self):
        """重写此方法返回要展示的用户模型对象"""
        return self.request.user


# PUT /email/
class EmailView(UpdateAPIView):
    """更新用户邮箱/"""

    permission_classes = []
    serializer_class = EmailSerializers

    def get_object(self):
        return self.request.user


class EmailVerifyView(APIView):
    """激活用户邮箱"""

    def get(self, request):

        # 获取前端查询字符串传入的token
        token = request.query_params.get('token')
        if not token:
            return Response({'message': '确少token'}, status=status.HTTP_400_BAD_REQUEST)

        #把token解密  并查询对应的user
        user = User.check_verify_email_token(token)
        #修改当前的user的email_active为True
        if user is None:
            return Response({'message':'激活失败'}, status=status.HTTP_400_BAD_REQUEST)
        user.email_active = True
        user.sava()
        #响应
        return Response({'message':'OK'})


class UserAddress(UpdateModelMixin, GenericViewSet):
    """用户收获地址增删查改"""

    permission_classes = [IsAuthenticated]
    serializer_class = UserAddressSerializer

    def get_queryset(self):
        return self.request.user.address.filter(is_deleted=True)

    def create(self, request):
        user = request.user
        # count = user.address.all().count()
        count = Address.objects.filter(user=user).count()
        if count >= 20:
            return Response({'message':'收获地址数量上限'}, status=status.HTTP_201_CREATED)

        #创建序列化器进行反序列化
        serializer = self.get_serializer(data=request.data)
        #调用序列化器的is_valid
        serializer.is_valid(raise_exception=True)
        #调用序列化器的save
        serializer.save()
        #
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # GET /address/
    def list(self, request, *args, **kwargs):
        """ 用户地址列表"""

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        user = self.request.user
        return Response({
            'user':user.id,
            'default_address_id':user.default_address_id,
            'limit':20,
            'address':serializer.data,
        })

    def destory(self, request, *args, **kwargs):
        """删除"""

        address = self.get_object()

        #进行逻辑删除
        address.is_deleted = True
        address.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
    @action(methods=['put'], detail=True)
    def title(self, request, pk=None):
        """修改标题"""

        address = self.get_object()
        serializer = AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

        # put /addresses/pk/status/

    @action(methods=['put'], detail=True)
    def title(self, request, pk=None):
        """修改标题"""
        address = self.get_object()
        serializer = AddressTitleSerializer(instance=address, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    # put /addresses/pk/status/
    @action(methods=['put'], detail=True)
    def status(self, request, pk=None):
        """设置默认地址"""

        address = self.get_object()
        request.user.default_address = address
        request.user.save()
        return Response({'message': 'OK'}, status=status.HTTP_200_OK)

class UserBrowserHistoryView(CreateAPIView):
    """用户商品浏览记录"""

    #指定序列化器
    serializer_class = UserBrowserHistorySerializer
    permission_classes = [IsAuthenticated]      #指定权限


    def get(self, request):
        """查询商品浏览记录"""

        #创建redis连接对象/
        redis_conn = get_redis_connection('history')

        #获取当前请求的用户
        user = request.user

        # 获取redis中当前用户的浏览记录列表数据
        sku_ids = redis_conn.lrange('history_%d' % user.id, 0, -1)

        # 把sku_id对应的sku模型查询 出来
        # SKU.objects.filter(id__in=sku_ids)  # 用此方式获取sku模型顺序就乱了
        sku_list = []
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            sku_list.append(sku)
        # 创建序列化器进行序列化器
        serializer = SKUSerializer(sku_list, many=True)

        # 响应
        return Response(serializer.data)



class UserAuthorizeView(ObtainJSONWebToken):
    """自定义账号密码登录视图,实现购物车登录合并"""
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user = serializer.object.get('user') or request.user
            token = serializer.object.get('token')
            response_data= jwt_response_payload_hendel(token, user, request)
            response = Response(response_data)
            if api_settings.JWT_AUTH_COOKIE:









