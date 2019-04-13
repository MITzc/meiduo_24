from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveAPIView
from rest_framework.mixins import ListModelMixin
from rest_framework_extensions.cache.mixins import CacheResponseMixin

from .models import Area
from .serializers import AreaSerializers, SubsSerializers


# Create your views here.


# class AreaListView(APIView):
#     """ 查询所有省 """
#     def get(self, request):
#
#         #1. 获取指定的查询集
#         qs = Area.objects.filter(parent=None)           #获取指定的查询集
#         #qs = Area.objects.all()
#         # 2. 创建序列化器进行序列化
#         serializer = AreaSerializers(qs, many=True)
#         # 3. 响应
#         return Response(serializer.data)



class AreaViewSet(AreaSerializers, SubsSerializers):

    # 指定查询集
    def get_queryset(self):
        if self.action == 'list':
            return Area.objects,filter(parent=True)
        else:
            return Area.objects.all()


    #指定序列化器
   # serializer_class =
    def get_serializer_class(self):
        if self.action = 'list':
            return AreaSerializers
        else:
            return SubsSerializers