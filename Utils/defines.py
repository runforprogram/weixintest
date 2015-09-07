# coding: utf-8

#常用http前置增加短路几率
SMALL_PROTOCOL_LIST = ('http://', 'https://')
PROTOCOL_LIST = ('http://', 'https://', 'ftp://', 'thunder://',
                 'ed2k://', 'flashget://', 'tencent://', 'mailto://', 'mms://', 'file:///', )

COMMON_TIME_STRING = "%Y-%m-%d %H:%M:%S"
COMMON_DATE_STRING = "%Y-%m-%d"

#接受的上传图片格式
ACCEPT_IMG_TYPE = (
    'jpg',
    'gif',
    'png',
    'bmp',
)

#数据类型与models对象映射
DATA_TYPES = {
    'department': 'Department',
    'site': 'Site',
    'mark': 'MarkSite',
    'visit': 'Visit',
    'worker': 'Worker',
}

#平台类型
PLATFORMS = ('ios', 'android')

#微信目前支持的功能
WX_FEATURES = [
    u'查询博尼施现有产品信息',
    u'查询员工信息',
    u'员工查询调休记录',
]

WX_FEATURES_STR = u"""
现有功能:
"""

index = 1
for feature in WX_FEATURES:
    WX_FEATURES_STR += u"%d: %s\n" % (index, feature)
    index += 1
WX_FEATURES_STR += u"\n支持语音或文本消息的模糊搜索。"
