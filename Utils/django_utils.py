# coding: utf-8

import json
import datetime
import os
import uuid
import urlparse as _urlparse

from functools import wraps
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import resolve_url
from django.utils.encoding import force_str
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.utils.decorators import available_attrs
from django.utils.six.moves.urllib.parse import urlparse
from django.contrib.auth.decorators import user_passes_test


from Utils import utils


LOGGER = utils.COMMON_LOGGER


require_superuser = user_passes_test(lambda u: u.is_superuser)
require_staff = user_passes_test(lambda u: u.is_staff)

def JsonResponse(ret, *args, **kwargs):
    return HttpResponse(json.dumps(ret, *args, **kwargs), content_type='application/json; charset=utf-8')


def JsonError(msg, **kwargs):
    ret = {
        'stat': 'error',
        'msg': msg,
    }
    ret.update(kwargs)
    return JsonResponse(ret)


def JsonSuccess(msg, **kwargs):
    ret = {
        'stat': 'success',
        'msg': msg,
    }
    ret.update(kwargs)
    return JsonResponse(ret)


def APIJsonSuccess(msg, **kwargs):
    ret = {
        'status': 1,
        'msg': msg,
    }
    ret.update(kwargs)
    return JsonResponse(ret, ensure_ascii=False)


def APIJsonError(msg, **kwargs):
    ret = {
        'status': 0,
        'msg': msg,
    }
    ret.update(kwargs)
    return JsonResponse(ret, ensure_ascii=False)


def JsonLog(msg, **kwargs):
    ret = {
        'stat': 'log',
        'msg': msg,
    }
    ret.update(kwargs)
    return JsonResponse(ret)


def get_object_or_none(model, **kwargs):
    return model.objects.filter(**kwargs).first()


def q_args_json(request):
    return json.dumps(dict(request.GET.lists()))


def get_sort_cond(request, sort_meta=(), default='-pk'):
    '''
    sort_meta = (
        ('create_time', 'sort_create_time'),
        ('price', 'sort_price'),
        ('distance', 'sort_distance'),
        ('launch_time', 'sort_launch_time'),
        )
    '''
    sort_cond = []
    for key, sort_key in sort_meta:
        val = request.GET.get(sort_key)
        if val == '1':
            sort_cond.append(key)
        if val == '-1':
            sort_cond.append('-'+key)
    return sort_cond if sort_cond else [default]


def filter_enable_city(request, q_set, filter_cond):
    enable_city = request.COOKIES.get('enable_city', '').strip('')
    without_city = request.GET.get('without_city')
    if not enable_city or without_city:
        return q_set
    return q_set.filter(filter_cond=enable_city)


class GenericQueryMixin(object):
    def query_enable_city(self, q_set, q_key):
        enable_city = self.request.COOKIES.get('enable_city', '')
        without_city = self.request.GET.get('without_city')
        if not enable_city or without_city:
            return q_set
        return q_set.filter(city__id=enable_city)


def upload_filepath(path_prefix='image'):
    def unique_filename(instance, filename):
        ext = filename.split('.')[-1]
        filename = "%s.%s" % (uuid.uuid4(), ext)
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        return os.path.join(path_prefix, today, filename)
    return unique_filename


def get_int(str_num):
    try:
        num = int(str_num)
        return num
    except ValueError:
        return 0


def get_float(str_num):
    try:
        num = float(str_num)
        return num
    except ValueError:
        return 0


def get_order_id():
    return uuid.uuid1().hex


def user_passes_test(test_func, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator for views that checks that the user passes the given test,
    redirecting to the log-in page if necessary. The test should be a callable
    that takes the user object and returns True if the user passes.
    """

    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            if request.is_ajax():
                return JsonError('请先登录。')
            path = request.build_absolute_uri()
            # urlparse chokes on lazy objects in Python 3, force to str
            resolved_login_url = force_str(
                resolve_url(login_url or settings.LOGIN_URL))
            # If the login url is the same scheme and net location then just
            # use the path as the "next" url.
            login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
            current_scheme, current_netloc = urlparse(path)[:2]
            if ((not login_scheme or login_scheme == current_scheme) and
                (not login_netloc or login_netloc == current_netloc)):
                path = request.get_full_path()
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(
                path, resolved_login_url, redirect_field_name)
        return _wrapped_view
    return decorator


def login_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated(),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def login_required_ajax(function=None):
    """
    Just make sure the user is authenticated to access a certain ajax view

    Otherwise return a HttpResponse 401 - authentication required
    instead of the 302 redirect of the original Django decorator
    """
    def _decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated():
                return view_func(request, *args, **kwargs)
            else:
                return HttpResponse(status=401)
        return _wrapped_view

    if function is None:
        return _decorator
    else:
        return _decorator(function)


def parse_put(request):
    payload = request.read()
    return dict(_urlparse.parse_qsl(payload))


def parse_put_list(request):
    payload = request.read()
    return _urlparse.parse_qs(payload)


def get_county_obj(province, city, county):
    from Main import models

    if not county:
        county = '其他'
    if not province:
        province = '其他'
    if not city:
        city = '其他'
    elif city in (u'襄樊市', '襄樊市'):
        city = '襄阳市'
    province_obj = models.Province.objects.get_or_create(name=province)[0]
    city_obj = models.City.objects.get_or_create(name=city,
                                                 province=province_obj)[0]
    county_obj = models.County.objects.get_or_create(name=county,
                                                     city=city_obj)[0]
    return county_obj


def media_url(request, path):
    if not path:
        return ''
    MEDIA_URL = settings.MEDIA_URL
    if not utils.is_absolute_url(MEDIA_URL):
        MEDIA_URL = request.build_absolute_uri(MEDIA_URL)
    return ''.join((MEDIA_URL, path))


def upload_file(file_id, file_content, file_type, file_storage='other'):
    today = datetime.datetime.now()
    year = str(today.year)
    month = str(today.month)
    day = str(today.day)
    file_name = '.'.join((file_id, file_type))
    file_folder= os.path.join(
        settings.MEDIA_ROOT,
        file_storage,
        year,
        month,
        day
    )
    if not os.path.exists(file_folder):
        os.makedirs(file_folder)
    file_path = os.path.join(file_folder, file_name)
    with file(file_path, 'w') as file_obj:
        file_obj.write(file_content)
    img_path = os.path.join(
        file_storage,
        year,
        month,
        day,
        file_name,
    )
    return img_path
