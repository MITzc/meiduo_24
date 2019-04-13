from django.conf.urls import url


from . import views


urlpatterns = [
    # 拼接QQ登录url
    url(r'^qq/authorization/$', views.QQOauthURLView.as_view()),
    # QQ登录后的回调
    url(r'^qq/user/$', views.QQOauthUserView.as_view()),
]