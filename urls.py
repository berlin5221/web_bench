#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Author: SunBolin
Date: 2016/06/13
Desc: web server urls.
"""

import tornado.web
from handlers.index import IndexHandler
from handlers.uploadfile import UploadFileHandler
from handlers.deploybench import DeployBenchHandler
from handlers.stopbench import StopBenchHandler
from handlers.getbenchrecords import GetBenchRecordsHandler
from handlers.getbenchstatus import GetBenchStatusHandler
from handlers.getwaitingtasks import GetWaitingTasksHandler

urls = [
        (r'/', IndexHandler),
        (r'/favicon.ico', tornado.web.StaticFileHandler, './static/'),
        (r'/robots.txt', tornado.web.StaticFileHandler, './static/'),
        (r'/results/*/results.html', tornado.web.StaticFileHandler, './static/'),
        (r'/bench/uploadconf', UploadFileHandler),
        (r'/bench/start', DeployBenchHandler),
        (r'/bench/stop', StopBenchHandler),
        (r'/bench/getrecords', GetBenchRecordsHandler),
        (r'/bench/getbenchstatus', GetBenchStatusHandler),
        (r'/bench/getwaitingtasks', GetWaitingTasksHandler),
    ]
