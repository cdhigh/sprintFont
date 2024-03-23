#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from contextlib import contextmanager
from functools import wraps
import datetime, logging, os, re, unittest
from unittest import mock    

logger = logging.getLogger('weedata')

class QueryLogHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        self.queries = []
        logging.Handler.__init__(self, *args, **kwargs)

    def emit(self, record):
        self.queries.append(record)

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self._qh = QueryLogHandler()
        logger.setLevel(logging.DEBUG)
        logger.addHandler(self._qh)

    def tearDown(self):
        logger.removeHandler(self._qh)

    def assertIsNone(self, value):
        self.assertTrue(value is None, '%r is not None' % value)

    def assertIsNotNone(self, value):
        self.assertTrue(value is not None, '%r is None' % value)

    @contextmanager
    def assertRaisesCtx(self, exceptions):
        try:
            yield
        except Exception as exc:
            if not isinstance(exc, exceptions):
                raise AssertionError('Got %s, expected %s' % (exc, exceptions))
        else:
            raise AssertionError('No exception was raised.')

    @property
    def history(self):
        return self._qh.queries

def skip_if(expr, reason='n/a'):
    def decorator(method):
        return unittest.skipIf(expr, reason)(method)
    return decorator

def skip_unless(expr, reason='n/a'):
    def decorator(method):
        return unittest.skipUnless(expr, reason)(method)
    return decorator
