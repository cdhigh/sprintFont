#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""Sprint-Layout v6 2022版的插件，在电路板插入其他字体（包括中文字体）的文字
使用cxFreeze打包成EXE文件
Author: cdhigh <https://github.com/cdhigh>
"""

import sys, os, re
from cx_Freeze import setup, Executable

if sys.platform == "win32":
    base = "Win32GUI"
else:
    base = None

APP_PATH = os.path.dirname(__file__)
#APP_LIB_PATH = os.path.normpath(os.path.join(APP_PATH, 'mylib'))
#sys.path.insert(0, APP_LIB_PATH)

appVersion = '1.0'
appMain = os.path.join(APP_PATH, 'sprintFont.py')
if os.path.exists(appMain):
    with open(appMain, 'r', encoding='utf-8') as f:
        slMain = f.read().split('\n')
    
    PATT_VERSION = r"^__VERSION__\s*=\s*[\"\']([0123456789.-]+)[\"\'](.*)"
    for line in slMain:
        mt = re.match(PATT_VERSION, line)
        if mt:
            appVersion = mt.group(1)
            break

build_exe_options = {'packages': ['tkinter'], 
                    'excludes' : ['pyQt5', 'PIL'],
                    'include_files' : [],
                    'optimize' : 2,
                    }

exe = Executable(script='sprintFont.py',
    initScript=None,
    base=base,
    target_name='sprintFont.exe')

setup(name='sprintFont', 
    version=appVersion,
    description='sprintFont - a plugin for Sprint-Layout',
    options={'build_exe': build_exe_options},
    executables=[Executable('sprintFont.py', base=base, icon='app.ico',)])