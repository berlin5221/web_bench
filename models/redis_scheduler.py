#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Author: SunBolin
Date: 2016/07/24
Desc: Scheduler with redis.
"""

from threading import Thread
import redis_pool
import subprocess
import redis
import logging
import time
import os

"""
1. 有正在执行的task，直接返回；
2. 没有正在执行的task，从待处理任务中取出下一个任务返回；
3. 同时从待处理任务中移除该任务，并将该任务存入到正在执行的任务中。
"""
get_task_script = "local ongoing_key = 'rcp_ongoing_task'; \
                   local ongoing_taskid = redis.call('get', ongoing_key); \
                   local res = {}; \
                   if (not ongoing_taskid) then \
                       local waiting_key = 'rcp_waiting_task'; \
                       local waiting_task0 = redis.call('zrange', waiting_key, 0, 0); \
                       if (table.maxn(waiting_task0) == 1) then \
                           local task_id = waiting_task0[1]; \
                           redis.call('set', ongoing_key, task_id); \
                           redis.call('zrem', waiting_key, task_id); \
                           res[1] = 'new'; \
                           res[2] = task_id; \
                       else \
                           return nil; \
                       end; \
                   else \
                       res[1] = 'ongoing'; \
                       res[2] = ongoing_taskid; \
                   end; \
                   return res; \
                   "

clear_expired_script = "local expired_tt = ARGV[1]; \
                        local bench_records_key = 'rcp_bench_records'; \
                        local expired_records = redis.call('zrangebyscore', bench_records_key, \
                            0, expired_tt); \
                        if (table.maxn(expired_records) > 0) then \
                            for index = 1,table.maxn(expired_records),1 do \
                                local task_id = expired_records[index]; \
                                local bench_task = 'br;'..task_id; \
                                redis.call('zrem', bench_records_key, task_id); \
                                redis.call('del', bench_task); \
                            end; \
                        end; \
                        "

class RedisScheduler(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.running = True
        self.redis_cli = redis.Redis(connection_pool=redis_pool.NORMAL_CONNECTION_POOL)

    def run(self):
        while self.running:
            """
            1. 查redis任务队列，有任务则启动；
            2. 启动任务后把正在执行的任务写入redis，防止任务hang住没法退出，同时方便查询.
            3. 每隔5分钟进行一次任务扫描；
            4. 定时任务到达时，需要逻辑比较复杂，要考虑定时任务是否能在该时段运行。
            """
            try:
                # 仅保留30天的压测记录.
                expired_tt = int(time.time()) - 30*3600*24
                self.redis_cli.eval(clear_expired_script, 1, 0, expired_tt)
                logging.info('clear expired bench records, expired_tt=%s' % expired_tt)
                res = self.redis_cli.eval(get_task_script, 0)
                if res:
                    task_id = res[1]
                    if 'new' == res[0]:
                        self.start_bench_task(task_id)
                    elif 'ongoing' == res[0]:
                        self.check_bench_task(task_id)
                # sleep 5 mins.
                time.sleep(300)
            except Exception as e:
                logging.error('failed to deploy task with exception %s' % e);

    def start_bench_task(self, task_id):
        key = 'br;%s' % task_id
        fileds = ['agent_num', 'duration', 'urls_conf', 'test_name', 'domain']
        task_info = self.redis_cli.hmget(key,fileds)
        agent_num = task_info[0]
        duration = task_info[1]
        conf_path = task_info[2]
        test_name = task_info[3]
        domain = task_info[4]
        pp = subprocess.Popen(['nohup', '/usr/bin/python2.7', './rcp_bench/start_bench.py',\
                                task_id, agent_num, duration, conf_path, test_name, domain])
        pid = pp.pid
        self.save_task_pid(pid, task_id, duration)
        pp.wait()

    def save_task_pid(self, pid, task_id, duration):
        key = 'pid;%s' % task_id
        logging.info('bench task started. save pid:%s taskid:%s' % (pid, task_id))
        self.redis_cli.setex(key, pid, int(duration)+10)

    def check_bench_task(self, task_id):
        # 检查压测进程是否存在，若不存在则清理脏数据.
        key = 'pid;%s' % task_id
        task_pid = self.redis_cli.get(key)
        if task_pid:
            try:
                os.kill(int(task_pid), 0)
            except OSError as e:
                logging.info('bench task process is not exist, clear ongoing key.')
                # 清理ongoing
                key = 'rcp_ongoing_task'
                self.redis_cli.delete(key)

    def stop(self):
        self.running = False
