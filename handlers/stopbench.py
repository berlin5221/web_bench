#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Author: SunBolin
Date: 2016/06/28
Desc: stop bench test.
"""
import tornado.web
import tornado.gen
import logging
import os
import signal
import time
from models import tornadoredis
from models import redis_pool


"""
用户终止正在运行的任务时：
1. 获取pid，若key不存在，任务可能在等待队列;
2. 从等待队列中移除该任务；
3. 若任务正在运行中，则删除rcp_ongoing_task;
"""
quit_task_script = "local task_id = ARGV[1]; \
                    local pid_key = 'pid;'..task_id; \
                    local task_pid = redis.call('get', pid_key); \
                    local waiting_key = 'rcp_waiting_task'; \
                    redis.call('zrem', waiting_key, task_id); \
                    local ongoing_key = 'rcp_ongoing_task'; \
                    local ongoing_task = redis.call('get', ongoing_key); \
                    if (ongoing_task == task_id) then \
                        redis.call('del', ongoing_key); \
                    end; \
                    redis.call('del', pid_key); \
                    return task_pid; \
                    "

class StopBenchHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.title = 'StopBench'

    def get(self):
        try:
            task_id = self.get_argument('task_id')
        except tornado.web.MissingArgumentError:
            errMsg = 'Missing argument %s.' % e.arg_name
            return self.return_err(1001, errMsg)
        return self.stop_bench_task(task_id)

    @tornado.web.asynchronous
    @tornado.gen.engine
    def stop_bench_task(self, task_id):
        redis_client = tornadoredis.Client(connection_pool=redis_pool.CONNECTION_POOL,
                password='pwd')
        pid = yield tornado.gen.Task(redis_client.eval, quit_task_script, args=[task_id])
        # stop process by pid.
        if pid:
            try:
                os.kill(int(pid), signal.SIGTERM)
                logging.info('rcp task quited, pid=%s' % pid)
            except OSError as e:
                logging.error('pid:%s not exist.' % pid)

        # set task status.
        key = 'br;%s' % task_id
        field_map = {}
        field_map['status'] = 'quit'
        now = time.strftime('%Y/%m/%d %H:%M:%S', time.localtime())
        field_map['finish_time'] = now
        yield tornado.gen.Task(redis_client.hmset, key, field_map)

        # add record.
        record_key = 'rcp_bench_records'
        score = long(time.time())
        yield tornado.gen.Task(redis_client.zadd, record_key, score, task_id)

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

