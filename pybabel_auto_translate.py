#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#自动翻译和更新po文件
#Author: cdhigh <https://github.com/cdhigh>
import os, sys, datetime, shutil
sys.path.insert(0, 'D:/Programer/Project/autopo')
from autopo import createAiAgent, translateFile

cfgFile = 'D:/Programer/Project/autopo/google.json'

thisDir = os.path.dirname(os.path.abspath(__file__))
bakDir = os.path.join(thisDir, 'tests', 'pobackup')
refPoFile = os.path.join(thisDir, 'i18n', 'zh_cn', 'LC_MESSAGES', 'messages.po')
refLang = 'zh_cn'

startTime = datetime.datetime.now()
agent = createAiAgent(cfgFile)
excluded = ['sprintFont', 'PTH/SMD', 'PTH pad', 'SMD pad']
for lang in ['de', 'es', 'pt', 'fr', 'ru', 'tr']:
    fileName = os.path.join(thisDir, 'i18n', lang, 'LC_MESSAGES', 'messages.po')
    shutil.copy(fileName, os.path.join(bakDir, f'{lang}.po')) #先备份
    translateFile(fileName=fileName, agent=agent, dstLang=lang, srcLang='en',
        refPoFile=refPoFile, refLang=refLang, fuzzify=False, excluded=excluded)

consumed = datetime.datetime.now() - startTime
print(f'Time consumed: {str(consumed).split(".")[0]}')

#如果新增翻译语种，需要检查这几个翻译的长度
#"     Font     ", "   Footprint  ",, "  SVG/Qrcode  ", "  Autorouter  ",
#"  Teardrop    ", " RoundedTrack "
os.system('pause')
