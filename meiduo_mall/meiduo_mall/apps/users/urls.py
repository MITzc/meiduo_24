
from django.conf.urls import url
from rest_framework_jwt.views import obtain_jwt_token
from rest_framework import routers


from . import views


urlpatterns = [
    # 注册用户
    url(r'^users/$', views.UserView.as_view()),
    # 判断用户名是否已注册
    url(r'^usernames/(?P<username>\w{5,20})/count/$', views.UsernameCountView.as_view()),
    # 判断手机号是否已注册
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),

    # JWT登录
    url(r'^authorizations/$', obtain_jwt_token),  # 内部认证代码还是Django  登录成功生成token
    # url(r'^authorizations/$',  ObtainJSONWebToken.as_view()),
    #获取用户详情
    url(r'^user/$', views.UserDetailView.as_view()),
    #更新邮箱
    url(r'^email/$', views.EmailView.as_view()),
    #验证邮箱
    url(r'^emails/verification/$', views.EmailVerifyView.as_view()),
    #商品浏览记录
    url(r'^browse_histories/$', views.UserBrowserHistoryView.as_view())
]

route = routers.DefaultRouters()
routers.register(r'address', views.AddressViewSet, base_name='addresses')
urlpatterns += routers.urls