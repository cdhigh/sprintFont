#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import re, os, shutil, sys, unittest, importlib, builtins
try:
    import coverage
except ImportError:
    coverage = None

builtins.__dict__['_'] = lambda x: x

testDir = os.path.dirname(__file__)
appDir = os.path.abspath(os.path.join(testDir, '..'))
sys.path.insert(0, appDir)

def runtests(suite, verbosity=1, failfast=False):
    runner = unittest.TextTestRunner(verbosity=verbosity, failfast=failfast)
    results = runner.run(suite)
    return results.failures, results.errors

def collect_tests(module=None):
    suite = unittest.TestSuite()
    modules = [module] if module else TEST_MODULES
    for target in modules:
        m = reload_module(target)
        user_suite = unittest.TestLoader().loadTestsFromModule(m)
        suite.addTest(user_suite)
    return suite

def reload_module(module_name):
    module = importlib.import_module(module_name)
    importlib.reload(module)
    return module

def start_test(verbosity=1, failfast=0, testonly='', report=''):
    if report and coverage:
        cov = coverage.coverage()
        cov.start()

    runtests(collect_tests(testonly), verbosity, failfast)
        
    if report and coverage:
        cov.stop()
        cov.save()
        if report == 'html':
            cov.html_report(directory=os.path.join(testDir, '.cov_html'))
        else:
            cov.report()

TEST_MODULES = ['test_base', 'test_kicad_to_sprint']

if __name__ == '__main__':
    verbosity = 1 #Verbosity of output
    failfast = 1 #Exit on first failure/error
    report = 'html' # 'html'|'text'|'', if debug in IDE, set to ''
    testonly = '' #module name, empty for testing all

    os.environ['KICAD_FOOTPRINT_DIR'] = '' #set this

    sys.exit(start_test(verbosity, failfast, testonly, report))
