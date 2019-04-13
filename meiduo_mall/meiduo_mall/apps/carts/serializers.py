from rest_framework import serializers


from goods.models import SKU



class CartSerializer(serializers.Serializer):
    """ 购物车序列化器 """

    sku_id = serializers.IntegerField(label='商品id',min_value=1 )
    count = serializers.IntegerField(label='购买数量')
    selected = serializers.BooleanField(label='商品勾选状态', default=True)

    def validate_sku_id(self, value):
        try:
            SKU.objects.get(id=value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('SKU不存在')
        return value


class SKUCartSerializer(serializers.Serializer):
    """ 购物车查询序列化器 """
    count = serializers.IntegerField(label='购买数量')
    selected = serializers.BooleanField(label='商品勾选状态')

    class Meta:
        model = SKU
        fields = ['id', 'name', 'price', 'defult_image_url', 'count', 'selected']



class CartDeleteSerializer(serializers.Serializer):
    """购物车删除序列化器"""
    sku_id = serializers.IntegerField(label='商品id', min_value=1)

    def validate_sku_id(self, value):
        try:
            SKU.objects.get(id=value)
        except SKU.DoesNotExist:
            raise serializers.ValidationError('SKU 不存在')
        return value



class CartSelectedAllSerilizer(serializers.Serializer):
    """ 购物车全选序列化器 """

    serializers = serializers.BooleanField(label='商品是否全选', )

