#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Author: SunBolin
Date: 2016/06/13
Desc: bench record handler.
"""
import tornado.web
import tornado.gen
import logging
from models import tornadoredis
from models import redis_pool


"""
get bench records.
传入参数：appid, _sid
返回结果：详情array.
"""
get_bench_records_script = "local appid = ARGV[1]; \
                            local _sid = ARGV[2]; \
                            local records_key = 'rcp_bench_records'; \
                            local bench_records = redis.call('zrevrange', records_key, \
                                0, -1); \
                            local record_infos = {}; \
                            if (table.maxn(bench_records) > 0) then \
                                local count = 1; \
                                for index = 1,table.maxn(bench_records),1 do \
                                    local bench_task = 'br;'..bench_records[index]; \
                                    local record_info = redis.call('hmget', bench_task, \
                                        'test_name', 'duration', 'start_time', 'finish_time', \
                                        'status', 'operator', 'appid', '_sid'); \
                                    if (((appid == '0') or (appid ~= '0' and record_info[7] == appid)) and \
                                        ((_sid == '0') or (_sid ~= '0' and record_info[8] == _sid))) then \
                                        table.insert(record_info, 1, bench_records[index]); \
                                        record_infos[count] = record_info; \
                                        count = count + 1; \
                                    end; \
                                end; \
                            end; \
                            return record_infos; \
                            "

class BenchRecordsHandler(tornado.web.RedirectHandler):
    def initialize(self):
        self.title = 'BenchRecord!'

    def get(self):
        try:
            page = self.get_argument('page')
            page_size = self.get_argument('pageSize')
            appid = self.get_argument('appid', default='0')
            _sid = self.get_argument('_sid', default='0')
        except tornado.web.MissingArgumentError as e:
            errMsg = 'Missing argument %s.' % e.arg_name
            return self.return_err(1001, errMsg)

        try:
            page_int = int(page)
            page_size_int = int(page_size)
            if page_int <= 0 or page_size_int <= 0:
                self.return_err(1003, 'Invalid argument')
        except ValueError as e:
             errMsg = 'Invalid argument type %s.' % e
             return self.return_err(1002, errMsg)

        return self.get_records(page_int, page_size_int, appid, _sid)

    @tornado.web.asynchronous
    @tornado.gen.engine
    def get_records(self, page, page_size, appid, _sid):
        start = (page - 1) * page_size
        end_index = start + page
        redis_client = tornadoredis.Client(connection_pool=redis_pool.CONNECTION_POOL,
                password='pwd')
        record_infos = yield tornado.gen.Task(redis_client.eval, get_bench_records_script,
                args=[appid, _sid])

        records = []
        records_count = len(record_infos)
        end_index = min(end_index, records_count)
        if start < records_count:
            for index in range(start, end_index):
                record_info = record_infos[index]
                record_info_map = {}
                record_info_map['task_id'] = record_info[0]
                record_info_map['test_name'] = record_info[1]
                record_info_map['duration'] = record_info[2]
                record_info_map['start_time'] = record_info[3]
                record_info_map['finish_time'] = record_info[4]
                record_info_map['status'] = record_info[5]
                record_info_map['operator'] = record_info[6]
                record_info_map['appid'] = record_info[7]
                record_info_map['_sid'] = record_info[8]
                records.append(record_info_map)

        logging.info('Bench record res, count=%s start=%s page_size=%s' \
                % (records_count, page, page_size))
        total_page = 0
        if records_count % page_size > 0:
            total_page = records_count/page_size + 1
        else:
            total_page = records_count/page_size

        resp = {}
        resp['errNo'] = 0
        resp['errMsg'] = 'success'
        resp['totalPage'] = total_page
        resp['records'] = records
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

