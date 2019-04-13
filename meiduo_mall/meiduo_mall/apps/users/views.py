from django.shortcuts import render
from rest_framework.generics import GenericAPIView, CreateAPIView, RetrieveAPIView,
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import CreateUserSerializer



from .models import User
from .serializers import UserDetailSerializer,


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
    serializer_class = UserDetailSerializer

