#!/usr/bin/env python
# coding: utf-8
import sha

import logging
import requests
import random
from uuid import uuid1
from bs4 import BeautifulSoup

import defines
import display
from Conf import config
from StringIO import StringIO


def get_common_logger(name='common', logfile=None):
    '''
    参数: name (str): logger name
        logfile (str): log file, 没有时使用stream handler
    返回:
        logger obj
    '''
    my_logger = logging.getLogger(name)
    my_logger.setLevel(config.LOG_LEVEL)
    if logfile:
        handler = logging.FileHandler(logfile)
    else:
        handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)s - %(message)s')
    handler.setFormatter(formatter)
    my_logger.addHandler(handler)
    #阻止冒泡
    my_logger.propagate = False
    return my_logger


COMMON_LOGGER = get_common_logger('common logger')


def add_http(url):
    '''给没有传输协议的url添加默认http://
    '''
    is_absolute = is_absolute_url(url)
    if not is_absolute:
        url = 'http://' + url
    return url


def is_absolute_url(url):
    is_absolute = False

    for pro in defines.SMALL_PROTOCOL_LIST:
        if url.startswith(pro):
            is_absolute = True
            break
    return is_absolute


def add_spider_header(request_session):
    request_session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-encoding": "gzip,deflate,sdch",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Accept-Language": "zh-CN,zh;q=0.8,en;q=0.6",
    })


def simple_get_html_by_url(url, timeout=10, params=None, host=None, length=None, post=None, response=False):
    '''
    传入合法url，获得html源码

    @type str
    @parm url
        timeout 超时时间
        host    指定host, IP爬取时需要
        length  获取html长度，None时为全部
        post    dict, 需要post的数据
        response 是否直接返回response对象
        params get传参

    @rtype str
    @return html

    @exception urlError
    '''
    siteurl = add_http(url)
    html = ''
    request_session = requests.Session()
    add_spider_header(request_session)
    if host:
        request_session.headers['Host'] = host
    try:
        if post:
            res = request_session.post(siteurl, data=post, timeout=timeout, stream=True)
        elif params:
            res = request_session.post(siteurl, data=post, params=params, timeout=timeout, stream=True)
        else:
            res = request_session.get(siteurl, timeout=timeout, stream=True)
        if response:
            return res
        if length:
            html = res.iter_content(chunk_size=length).next()
        else:
            html = res.content
    except Exception:
        COMMON_LOGGER.exception('Cannot open url: %s' % siteurl)
        return False
    return html


def json_default(obj):
    '''Default JSON serializer for our project.'''
    import datetime

    if isinstance(obj, datetime.datetime):
        return str(obj)


def dict_exchange(obj):
    return {v: k for k, v in obj.iteritems()}


def get_code(num):
    '''Generate a random str in length num
    '''
    return ''.join(random.sample([chr(i) for i in range(48, 58) + range(65, 91) + range(98, 123)] * 3, num))


def get_num_code(num):
    '''Generate a random num str in length num
    '''
    return ''.join(random.sample([chr(i) for i in range(48, 58)] * 10, num))


def admin_upload(file_obj, file_name=None):
    from async_utils import ftp_upload

    if not file_name:
        file_name = file_obj.__dict__.get('_name', '')
        file_name = '%s_%s' % (uuid1().get_hex(), file_name.split('.')[-1])
    loaded_obj = StringIO(file_obj.read())
    ftp_upload(file_name, loaded_obj)
    file_url = '%s%s' % (config.ADMIN_UPLOAD, file_name)
    return file_url


def get_display(word, sub='default'):
    '''获取展示映射
    '''
    try:
        ret = display.DISPLAY_MAP.get(word, word)
        if type(ret) == dict:
            ret = ret.get(sub, ret['default'])
    except TypeError:
        COMMON_LOGGER.exception('Unhashable!')
        ret = word
    return ret

def get_week_day(dt):
    week_day_map = {
        '1': '周一',
        '2': '周二',
        '3': '周三',
        '4': '周四',
        '5': '周五',
        '6': '周六',
        '7': '周末',
    }
    return week_day_map[dt.strftime("%w")]

def site_prop(site):
    if site.data_type == 'site':
        site_type = site.site_type
        sign_type = site.sign_type
        site_kind = site.site_kind
        ret_list = []
        for word in (site_type, sign_type, site_kind):
            if word:
                display = get_display(word)
                ret_list.append(display)
        return u'/'.join(ret_list)
    elif site.data_type == 'mark':
        site_type = site.site_type
        site_kind = site.site_kind
        ret_list = []
        for word in (site_type, site_kind):
            if word:
                display = get_display(word)
                ret_list.append(display)
        return u'/'.join(ret_list)
    elif site.data_type == 'department':
        return get_display(site.department_type)
    return ''


def brand_class(site):
    class_data = site.truck_class.all()
    truck_class = class_data.first()
    ret = ''
    if truck_class:
        truck_brand_name = truck_class.truck_brand.name
        ret += '%s/' % truck_brand_name
    else:
        return '无'
    try:
        ret += u'、'.join(truck_class.name for truck_class in class_data)
    except Exception:
        ret = u'无'
    return ret


def site_maintainer(site):
    try:
        maintainer = site.maintainer
    except Exception:
        return '无', '无'
    if not maintainer:
        return '无', '无'
    maintainer_info = maintainer.name
    if maintainer.phone:
        maintainer_info += ' (%s)' % maintainer.phone
    job_role = maintainer.job_role()
    return job_role, maintainer_info


def site_contacts(site):
    try:
        contacts = site.contacts or u'无'
    except Exception:
        contacts = u'无'
    try:
        site_phone = site.site_phone or u'无'
    except Exception:
        site_phone = u'无'
    return u'%s(%s)' % (contacts, site_phone)


class StreamBuffer(object):

    def write(self, value):
        return value


def force_gbk(my_str):
    ret = my_str
    if isinstance(my_str, basestring):
        if isinstance(my_str, unicode):
            try:
                ret = my_str.encode("GBK")
            except:
                ret = ''
        else:
            try:
                ret = my_str.decode("utf-8").encode("GBK")
            except:
                ret = ''
    return ret


def site_csv_row(site):
    truck_class_obj = site.truck_class.first()
    if truck_class_obj:
        truck_brand = truck_class_obj.truck_brand.name
        truck_class = ','.join(truck_class.name for truck_class in site.truck_class.all())
    else:
        truck_brand = ''
        truck_class = ''
    try:
        site_code = site.site_code
    except Exception:
        site_code = ''
    try:
        county_obj = site.county
    except Exception:
        county_obj = None
    if county_obj:
        county = county_obj.name
        city = county_obj.city.name
        province = county_obj.city.province.name
    else:
        province = ''
        city = ''
        county = ''
    address = site.address or ''
    contacts = site.contacts or ''
    site_phone = site.site_phone or ''
    try:
        site_kind = get_display(site.site_kind)
    except Exception:
        site_kind = ''
    try:
        site_type = get_display(site.site_type)
    except Exception:
        site_type = ''
    try:
        sign_type = get_display(site.sign_type)
    except Exception:
        sign_type = ''
    try:
        department_type = get_display(site.department_type)
    except Exception:
        department_type = ''
    try:
        member_count = site.member_count
    except Exception:
        member_count = 0
    try:
        maintainer_obj = site.maintainer
        maintainer = maintainer_obj.name
        maintainer_phone = maintainer_obj.phone
    except Exception:
        maintainer = ''
        maintainer_phone = ''
    try:
        department = site.department.name
    except Exception:
        department = ''
    lng = site.lng
    lat = site.lat
    update_time = site.update_time
    create_time = site.create_time
    try:
        remark = site.remark
    except Exception:
        remark = ''
    ret = [
        force_gbk(site.name),
        force_gbk(site_code),
        force_gbk(truck_brand),
        force_gbk(truck_class),
        force_gbk(province),
        force_gbk(city),
        force_gbk(county),
        force_gbk(address),
        force_gbk(contacts),
        force_gbk(site_phone),
        force_gbk(site_kind),
        force_gbk(site_type),
        force_gbk(sign_type),
        force_gbk(department_type),
        force_gbk(str(member_count)),
        force_gbk(maintainer),
        force_gbk(maintainer_phone),
        force_gbk(department),
        force_gbk(str(lng)),
        force_gbk(str(lat)),
        force_gbk(str(update_time)),
        force_gbk(str(create_time)),
        force_gbk(remark),
    ]
    return ret


def worker_csv_row(worker):
    truck_class_obj = worker.truck_class.first()
    if truck_class_obj:
        truck_brand = truck_class_obj.truck_brand.name
        truck_class = ','.join(truck_class.name for truck_class in worker.truck_class.all())
    else:
        truck_brand = ''
        truck_class = ''
    department_obj = worker.department
    if department_obj:
        department = department_obj.name
    else:
        department = ''
    ret = [
        force_gbk(worker.name),
        force_gbk(department),
        force_gbk(worker.job_role()),
        force_gbk(worker.phone),
        force_gbk(get_display(worker.sex)),
        force_gbk(get_display(truck_brand)),
        force_gbk(get_display(truck_class)),
        force_gbk(str(worker.create_time or '')),
        force_gbk(str(worker.update_time or '')),
        force_gbk(str(worker.last_login_time or '')),
    ]
    return ret


def verify_wx(request):
    args = request.GET
    echostr = args.get('echostr', '')
    signature = args.get('signature', '')
    timestamp = args.get('timestamp', '')
    nonce = args.get('nonce', '')
    strings = [config.TOKEN, timestamp, nonce]
    strings.sort()
    v_string = ''.join(strings)
    v_string = sha.sha(v_string).hexdigest()
    if v_string == signature:
        return True
    else:
        return False

def html2text(html):
    return BeautifulSoup(html).get_text()


if __name__ == '__main__':
    #import doctest
    #print doctest.testmod()
    COMMON_LOGGER.debug('test')
    #print dict_exchange({'a':1, 'b':2})
    #print get_num_code(100)
    #print admin_upload(open('test', 'wb+'))
