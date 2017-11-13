#!/usr/bin/env python
# -*- coding:utf-8 -*-
'''
Author: SunBolin
Date: 2016/06/13
Desc: A tornado app.
'''
import tornado.web
from urls import urls
from settings import SETTINGS

class Application(tornado.web.Application):
    def __init__(self):
        handlers = urls
        settings = SETTINGS
        tornado.web.Application.__init__(self, handlers, **settings)

