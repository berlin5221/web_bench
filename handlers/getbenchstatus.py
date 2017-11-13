#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Author: SunBolin
Date: 2016/06/28
Desc: get bench status.
"""
import tornado.web
import tornado.gen
import logging
from models import tornadoredis
from models import redis_pool


class GetBenchStatusHandler(tornado.web.RedirectHandler):
    def initialize(self):
        self.title = 'GetBenchStatus'

    def get(self):
        try:
            task_id = self.get_argument('task_id')
        except tornado.web.MissingArgumentError as e:
            errMsg = 'Missing argument %s.' % e.arg_name
            return self.return_err(1001, errMsg)
        return self.get_bench_status(task_id)

    @tornado.web.asynchronous
    @tornado.gen.engine
    def get_bench_status(self, task_id):
        redis_client = tornadoredis.Client(connection_pool=redis_pool.CONNECTION_POOL,
                password='pwd')
        key = 'br;%s' % task_id
        record_map = yield tornado.gen.Task(redis_client.hgetall, key)

        resp = {}
        resp['errNo'] = 0
        resp['errMsg'] = 'success'
        resp['taskId'] = task_id
        resp['taskDetail'] = record_map

        resp_json = tornado.escape.json_encode(resp)
        self.write(resp_json)
        self.finish()

    def return_err(self, errNo, errMsg):
        resp = {}
        resp['errNo'] = errNo
        resp['errMsg'] = errMsg
        logging.warn('return err errNo=%s errMsg=%s' % (errNo, errMsg))
        self.write(resp)
        self.finish()

