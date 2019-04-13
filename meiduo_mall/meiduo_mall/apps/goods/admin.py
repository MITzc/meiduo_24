from django.contrib import admin

from . import models
# Register your models here.


class  GoodsCategoryAdmin(admin.ModelAdmin):
    """ 商品类别模型站点管理 """
    def save_model(self, request, obj, form, change):
        """

        :param request:
        :param obj:
        :param form:
        :param change:
        :return:
        """
        obj.save()

    def delete_model(self, request, obj):
        """ 当点击admin站点删除按钮会调用此方法 """
        obj.delete()

        pass
    


admin.site.register(models.GoodsCategory)
admin.site.register(models.GoodsChannel)
admin.site.register(models.Goods)
admin.site.register(models.Brand)
admin.site.register(models.GoodsSpecification)
admin.site.register(models.SpecificationOption)
admin.site.register(models.SKU)
admin.site.register(models.SKUSpecification)
admin.site.register(models.SKUImage)
