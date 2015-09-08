# coding=utf-8
import _mysql_exceptions
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from Utils import utils
from Utils.django_utils import APIJsonError

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

    #def get_arg(self, arg_key):

     #   return self.args.get(arg_key, '').strip()


class Verify(APIView):
    def get(self, request):
        args = request.GET
        print request.__str__
        echostr = args.get('echostr', '')
        print echostr
        if utils.verify_wx(request):
            return HttpResponse(echostr)
        else:
            return HttpResponse('Error Signature')

    def post(self, request):
        if utils.verify_wx(request):
            ret = self.handle_msg(request)
            LOGGER.debug(ret)
            return HttpResponse(ret)
        else:
            return HttpResponse('Error Signature')
