#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Author: SunBolin
Date: 2016/06/13
Desc: A tornado web server.
"""
import tornado.httpserver
import tornado.ioloop
from application import Application
import logging
import os.path

from models.redis_scheduler import RedisScheduler

from tornado.options import define, options
define('port', default=8080, help='run on the given port', type=int)
define('log_file_prefix', default=os.path.join(os.path.dirname(__file__), 'logs/tornado_server.log'))


def main():
    # add a bg thread to exec cron tab.
    scheduler = RedisScheduler()
    scheduler.setDaemon(True)
    scheduler.start()

    try:
        tornado.options.parse_command_line()
        http_server = tornado.httpserver.HTTPServer(Application())
        logging.info('tornado server started with port %s.' % (options.port))
        http_server.listen(options.port)
        tornado.ioloop.IOLoop.instance().start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.stop()
        logging.info('tornado server stopped.')

if __name__ == '__main__':
    main()
