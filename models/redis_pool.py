#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Author: SunBolin
Date: 2016/06/30
Desc: Redis connection pool.
"""
import tornadoredis
import redis

CONNECTION_POOL = tornadoredis.ConnectionPool(max_connections=10, wait_for_available=True,
        host='x.x.x.x', port=8379)
NORMAL_CONNECTION_POOL = redis.ConnectionPool(max_connections=10, host='x.x.x.x', port=8379,
        password='pwd', db=0)
