#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Author: SunBolin
Date: 2016/06/28
Desc: accept and save the uploaded file.
"""
import tornado.web
import os.path
import time
import logging

class UploadFileHandler(tornado.web.RedirectHandler):
    def initialize(self):
        self.title = 'UploadFile'

    def get(self):
        self.render('uploadfile.html')

    def post(self):
        upload_path = os.path.join(os.path.dirname(__file__), '../files')
        file_metas = self.request.files['file']
        for meta in file_metas:
            now = time.strftime('%Y%m%d%H%M%S',time.localtime(time.time()))
            filename = now + '_' + meta['filename']
            filepath = os.path.join(upload_path, filename)
            with open(filepath, 'wb') as upf:
                upf.write(meta['body'])
                logging.info('file:%s uploaded.' % filename)
        resp = {}
        resp['filepath'] = filename
        resp_json = tornado.escape.json_encode(resp)
        self.write(resp_json)
        self.finish()

