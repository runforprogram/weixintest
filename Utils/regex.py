#coding=utf-8
import re

RE_PHONE = re.compile(r'^(\d{5}|\d{3,4}(|-)\d{3,4}(|-)\d{3,4})$')
RE_IDENTIFI = re.compile(r'^[1-9]\d{5}[1-9]\d{3}((0\d)|(1[0-2]))(([0|1|2]\d)|3[0-1])(\d{3})(\d|x|X)$')
