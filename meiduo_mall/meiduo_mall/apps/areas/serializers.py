from rest_framework import serializers

from .models import Area

class AreaSerializers(serializers.ModelSerializer):
    """ 省的序列化器 """
    class Meta:
        model = Area,
        fields = ['id', 'name']


class SubsSerializers(serializers.ModelSerializer):
    """ 区域详情视图  """

    subs = AreaSerializers(many=True)
    # subs = serializers.PrimaryKeyRelatedField()  # 只会序列化出 id
    # subs = serializers.StringRelatedField()  # 序列化的时模型中str方法返回值


    class Meta:
        model = Area
        fields = ['id', 'name', 'subs']




