from django.conf.urls import url


from . import views


urlpatterns = {
    url(r'^order/Settlement/$', views.OrderSettlementView.as_view()),     #去结算
    url(r'^order/$', views.OrderCommitView.as_view()),          #保存订单
}




