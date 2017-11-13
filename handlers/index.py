#!/usr/bin/env python
# -*- coding:utf-8 -*-
'''
Author: SunBolin
Date: 2016/06/13
Desc: index handler.
'''
import tornado.web

class IndexHandler(tornado.web.RedirectHandler):
    def initialize(self):
        self.title = 'Index!'

    def get(self):
        self.render('index.html')

