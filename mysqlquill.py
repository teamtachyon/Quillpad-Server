# -*- coding: utf-8 -*-
# @Date    : Nov 22  2012
# @Author  : Ram Prakash
# @Version : 1

import cherrypy
import MySQLdb

def connect(thread_index):
	cherrypy.thread_data.db = MySQLdb.connect('127.0.0.1', 'quill', 'quill','quill')

cherrypy.server.on_start_thread_list.append(connect)

class Root:
	def index(self):
		c = cherrypy.thread_data.db.cursor()
		c.execute("select count(*) from error_log")
		res = c.fetchone()
		c.close()
		return "<html><body>Hello, you have %d records in your table</body></html>" % res[0]
	index.exposed = True

cherrypy.root = Root()
cherrypy.config.update(file='mysqlcherry.conf')
cherrypy.config.update({'thread_pool':10})
cherrypy.server.start()
