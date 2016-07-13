# -*- coding: utf-8 -*-
# @Date    : Jan 25, 2013
# @Author  : Ram Prakash, Sharath Puranik
# @Version : 1

import cherrypy

class HelloWorld:
    def index(self):
        return "Hello World!"
    index.exposed = True

cherrypy.root = HelloWorld()
cherrypy.server.start()
