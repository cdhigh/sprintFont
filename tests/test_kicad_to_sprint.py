#!/usr/bin/env python3
# -*- coding:utf-8 -*-
#当前测试是否出现异常，测试前需要设置环境变量，KICAD_FOOTPRINT_DIR
import os, glob
from collections import defaultdict
from test_base import *
from kicad_to_sprint import kicadModToTextIo, KicadMod, KicadMod8

class TestKicadToSprint(BaseTestCase):
    def test_convert_no_exceptions(self):
        fpDir = os.getenv('KICAD_FOOTPRINT_DIR')
        self.assertTrue(fpDir and os.path.exists(fpDir), 'env KICAD_FOOTPRINT_DIR have to been set')

        count = 0
        for fileName in glob.iglob(os.path.join(fpDir, '**/*.kicad_mod'), recursive=True):
            textIo = kicadModToTextIo(fileName, importText=True)
            if isinstance(textIo, str):
                print(textIo, ' --> ', fileName)
            else:
                count += 1
            if count % 100 == 0:
                print(f'{count} kicad_mod processed.')
        print(f'Finished.\n{count} kicad_mod files have been tested.')

