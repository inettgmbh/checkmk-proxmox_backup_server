#!/usr/bin/env python3
import ast

import mkp

f_info = open("info.json", "r")
info = ast.literal_eval(f_info.read())
f_info.close()

mkp.pack_to_file(info, '.', "%s-%s.mkp" % (info['name'], info['version']))
