# -*- coding: utf-8 -*-
# @Date    : Jan 25, 2013
# @Author  : Ram Prakash, Sharath Puranik
# @Version : 1

class _const(object):
    class ConstError(TypeError): pass
    def __setattr__(self, name, value):
        if name in self.__dict__:
            raise self.ConstError, "Can't rebind const(%s)" % name
        self.__dict__[name] = value
    def __delattr__(self, name):
        if name in self.__dict__:
            raise self.ConstError, "Can't unbind const(%s)" % name
        raise NameError, name

import sys
sys.modules[__name__] = _const( )
import const
const.optionSeperator = '---!!---'
const.langWordMark = '--WORD--'
const.gendir = "sc"

const.SMTP_SERVER_URL = "localhost"
const.SMTP_LOGIN_USER = ""
const.SMTP_LOGIN_PASSWD = ""