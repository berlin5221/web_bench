#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Author: SunBolin
Date: 2016/06/28
Desc: Deploy bench test.
"""
import tornado.web
import tornado.gen
import logging
import string
import random
import time
import os
from models import tornadoredis
from models import redis_pool


class DeployBenchHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.title = 'DeployBench'

    def get(self):
        try:
            # so far, only GET method supported.
            agent_num = self.get_argument('agent_num')
            duration = self.get_argument('duration')
            urls_conf = self.get_argument('urls_conf')
            test_name = self.get_argument('test_name')
            operator = self.get_argument('operator')
            appid = self.get_argument('appid', default='0')
            _sid = self.get_argument('_sid', default='0')
            domain = self.get_argument('domain', 'xxx')
        except tornado.web.MissingArgumentError as e:
            errMsg = 'Missing argument %s.' % e.arg_name
            return self.return_err(1001, errMsg)
        conf_path = './files/%s' % urls_conf

        try:
            agent_int = int(agent_num)
            duration_int = int(duration)
        except ValueError as e:
            errMsg = 'Invalid argument type %s.' % e
            return self.return_err(1002, errMsg)

        if not os.path.exists(conf_path):
            errMsg = 'urls conf file is not exists.'
            return self.return_err(1003, errMsg)

        # generate task id randomly.
        size = 6
        chars = string.ascii_uppercase + string.digits
        task_id = ''.join(random.choice(chars) for _ in range(size))
        return self.save_bench_task(task_id, appid, _sid, agent_num, duration,
                conf_path, test_name, operator, domain)

    @tornado.web.asynchronous
    @tornado.gen.engine
    def save_bench_task(self, task_id, appid, _sid, agent_num, duration,
            conf_path, test_name, operator, domain):
        redis_client = tornadoredis.Client(connection_pool=redis_pool.CONNECTION_POOL,
                password='pwd')
        key = 'br;%s' % task_id
        field_map = {}
        field_map['agent_num'] = agent_num
        field_map['duration'] = duration
        field_map['urls_conf'] = conf_path
        field_map['test_name'] = test_name
        field_map['operator'] = operator
        field_map['status'] = 'waiting'
        field_map['appid'] = appid
        field_map['_sid'] = _sid
        field_map['domain'] = domain
        res = yield tornado.gen.Task(redis_client.hmset, key, field_map)
        logging.info('save bench task to redis hset, task_id=%s' % task_id)

        # add task to waiting queue.
        waiting_key = 'rcp_waiting_task'
        score = int(time.time())
        res = yield tornado.gen.Task(redis_client.zadd, waiting_key, score, task_id)
        logging.info('add bench task to redis queue, score=%s task_id=%s' % (score, task_id))

        resp = {}
        resp['errNo'] = 0
        resp["errMsg"] = 'success'
        resp['task_id'] = task_id
        resp_json = tornado.escape.json_encode(resp)
        self.write(resp_json)
        self.finish()

    def return_err(self, errNo, errMsg):
        resp = {}
        resp['errNo'] = errNo
        resp['errMsg'] = errMsg
        logging.warn('return err errNo=%s errMsg=%s' % (errNo, errMsg))
        resp_json = tornado.escape.json_encode(resp)
        self.write(resp_json)
        self.finish()

