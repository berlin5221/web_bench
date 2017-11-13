#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
Author: SunBolin
Date: 2016/06/13
Desc: tornado settings.
"""
import os.path

SETTINGS = dict(
        template_path = os.path.join(os.path.dirname(__file__), 'templates'),
        static_path = os.path.join(os.path.dirname(__file__), 'static'),
    )
