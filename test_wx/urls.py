from django.conf.urls import patterns, include, url
from django.contrib import admin

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'test_wx.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^test_wx/',include('weixin.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
