#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Author: SunBolin
Date: 2016/09/06
Desc: Get waiting bench task list.
"""
import tornado.web
import tornado.gen
import logging
from models import tornadoredis
from models import redis_pool


"""
1. 查ongoing列表，查ongoing详情；
2. 查waiting列表，查waiting详情.
"""
get_waiting_tasks_script = "local res = {}; \
                            local ongoing_key = 'rcp_ongoing_task'; \
                            local ongoing_taskid = redis.call('get', ongoing_key); \
                            local ongoing_info = {}; \
                            if ongoing_taskid then \
                                local ongoing_task = 'br;'..ongoing_taskid; \
                                ongoing_info = redis.call('hmget', ongoing_task, \
                                    'test_name', 'duration', 'start_time', \
                                    'operator', 'appid', '_sid'); \
                                table.insert(ongoing_info, 1, ongoing_taskid); \
                            end; \
                            res[1] = ongoing_info; \
                            local waiting_infos = {}; \
                            local waiting_key = 'rcp_waiting_task'; \
                            local waiting_tasks = redis.call('zrange', waiting_key, 0, -1); \
                            if (table.maxn(waiting_tasks) > 0) then \
                                for index = 1,table.maxn(waiting_tasks),1 do \
                                    local waiting_task = 'br;'..waiting_tasks[index]; \
                                    local waiting_info = redis.call('hmget', waiting_task, \
                                        'test_name', 'duration', 'operator', 'appid', '_sid'); \
                                    table.insert(waiting_info, 1, waiting_tasks[index]); \
                                    waiting_infos[index] = waiting_info; \
                                end; \
                            end; \
                            res[2] = waiting_infos; \
                            return res; \
                            "

class GetWaitingTasksHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.title = 'GetWaitingTasks'

    def get(self):
        appid = self.get_argument('appid', default='0')
        _sid = self.get_argument('_sid', default='0')
        return self.get_waiting_tasks(appid, _sid)

    @tornado.web.asynchronous
    @tornado.gen.engine
    def get_waiting_tasks(self, appid, _sid):
        redis_client = tornadoredis.Client(connection_pool=redis_pool.CONNECTION_POOL,
                password='pwd')

        res = yield tornado.gen.Task(redis_client.eval, get_waiting_tasks_script)
        ongoing_info = res[0]
        waiting_infos = res[1]

        ongoing_info_list = []
        if ongoing_info and ('0' == appid or (appid != '0' and ongoing_info[5] == appid)) and \
                ('0' == _sid or (_sid != '0' and ongoing_info[6] == _sid)):
            ongoing_info_map = {}
            ongoing_info_map['task_id'] = ongoing_info[0]
            ongoing_info_map['test_name'] = ongoing_info[1]
            ongoing_info_map['duration'] = ongoing_info[2]
            ongoing_info_map['start_time'] = ongoing_info[3]
            ongoing_info_map['operator'] = ongoing_info[4]
            ongoing_info_map['appid'] = ongoing_info[5]
            ongoing_info_map['_sid'] = ongoing_info[6]
            ongoing_info_list.append(ongoing_info_map)

        waiting_info_list = []
        for waiting_info in waiting_infos:
            if waiting_info and ('0' == appid or (appid != '0' and waiting_info[4] == appid)) and \
                    ('0' == _sid or (_sid != '0' and waiting_info[5] == _sid)):
                waiting_info_map = {}
                waiting_info_map['task_id'] = waiting_info[0]
                waiting_info_map['test_name'] = waiting_info[1]
                waiting_info_map['duration'] = waiting_info[2]
                waiting_info_map['operator'] = waiting_info[3]
                waiting_info_map['appid'] = waiting_info[4]
                waiting_info_map['_sid'] = waiting_info[5]
                waiting_info_list.append(waiting_info_map)

        resp = {}
        resp['ongoing_infos'] = ongoing_info_list
        resp['waiting_infos'] = waiting_info_list
        resp['errNo'] = 0
        resp["errMsg"] = 'success'

        resp_json = tornado.escape.json_encode(resp)
        self.write(resp_json)
        self.finish()

