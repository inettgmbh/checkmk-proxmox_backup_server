#!/usr/bin/env python3

from sys import argv
import ast
import pprint

# read info.json file
f_info = open("info.json", "r")
info = ast.literal_eval(f_info.read())
info['version'] = argv[1]
f_info.close()

# write info.json file
f_info = open("info.json", "w")
pprint.pprint(info, stream=f_info)
# f_info.write(pprint.saferepr(package.info.json))
f_info.close()
