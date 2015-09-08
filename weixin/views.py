# coding=utf-8
from xml.dom import minidom
import _mysql_exceptions
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import time
from Utils import utils
from Utils.django_utils import APIJsonError
from weixin import xml_templates

LOGGER = utils.COMMON_LOGGER


class APIView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        if settings.DEBUG:
            payload = self.request.POST.urlencode()
            if payload:
                LOGGER.debug('Payload:%s' % payload)
        try:
            return super(APIView, self).dispatch(request,*args, **kwargs)
        except _mysql_exceptions.Warning:
            LOGGER.exception('Mysql save error')
            return APIJsonError(u'输入不合法')

    def get_arg(self, arg_key):
        return self.args.get(arg_key, '').strip()


class Verify(APIView):
    def get(self, request):
        args = request.GET
        echostr = args.get('echostr', '')
        if utils.verify_wx(request):
            return HttpResponse(echostr)
        else:
            return HttpResponse('Error Signature')
    def post(self, request):
        LOGGER.debug("this is for test in post")
        if utils.verify_wx(request):
            ret = self.handle_msg(request)
            LOGGER.debug(ret)
            return HttpResponse(ret)
        else:
            return HttpResponse('Error Signature')

    def handle_msg(self, request):
        self.msg_dict=self.parse_msg(request.body)
        if not self.msg_dict:
            return ''
        msg=self.msg_dict.get('msg')
        openid=self.msg_dict.get('to_user_name')
        msg=u'无法识别你说的 %s，'%(self.msg_dict.get('msg',''))
        self.msg_dict['msg']=msg
        ret=self.auto_reply_text()
        return  ret

    def parse_msg(self, body):
        LOGGER.debug(body)
        msg_obj=minidom.parseString(body)
        msg_type_list=msg_obj.getElementsByTagName('MsgType')
        if not msg_type_list:
            return {}
        msg_type=msg_type_list[0].firstChild.nodeValue
        msg_list=[]
        from_user_name=msg_obj.getElementsByTagName('FromUserName')[0].firstChild.nodeValue
        to_user_name=msg_obj.getElementsByTagName('ToUserName')[0].firstChild.nodeValue
        if str(msg_type)=='text':
            msg_list=msg_obj.getElementsByTagName('Content')
        if not msg_list:
            return {}
        msg=msg_list[0].firstChild.nodeValue
        self.msg=msg
        self.user_id=from_user_name
        self.our_id=to_user_name

        return {
            'msg':msg,
            'from_user_name':self.our_id,
            'to_user_name':self.user_id,
        }

    def auto_reply_text(self):
        #self.force_utf8()
        return  xml_templates.TEXT_REPLY %(
            self.msg_dict.get('to_user_name',''),
            self.msg_dict.get('from_user_name',''),
            int(time.time()),
            self.msg_dict.get('msg','')
        )


