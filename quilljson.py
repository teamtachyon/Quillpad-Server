# -*- coding: utf-8 -*-
# @Date    : Nov 22  2012
# @Author  : Ram Prakash
# @Version : 1

def dictToJSON(d):
    str = "{"
    for i in d:
        str += jsonmap[type(i)](i) + ": "
        str += jsonmap[type(d[i])](d[i]) + ", "
    if len(d.keys()) > 0:
        str = str[:-2]
    str += "}"
    return str

def boolToJSON(b):
    if b:
        return "true"
    else:
        return "false"

def listToJSON(b):
    str = "["
    for i in b:
        str += jsonmap[type(i)](i) + ", "
    if len(b) > 0:
        str = str[:-2]
    str += "]"
    return str

jsonmap = {
    type([]): listToJSON,
    type(()): listToJSON,
    type({}): dictToJSON,
    type(""): lambda x: '"%s"' % (x),
    type(0): lambda x: str(x),
    type(u""): lambda x: '"' + x + '"',
    type(0.1): lambda x: str(x),
    type(True): boolToJSON,
    type(None): lambda x: "null"
}

def encode(dict):
    if type(dict) != type({}):
        raise Exception("Expected a dictionary")

    return dictToJSON(dict)
