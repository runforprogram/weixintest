from django.conf.urls import patterns, url
from weixin import views

__author__ = 'Administrator'

urlpatterns=patterns('',
    # url(r'^blog/', include('blog.urls')),
    url(r'^verify/',views.Verify.as_view(),name='rest_verify',)
)

