# -*- coding: utf-8 -*-
# @Date    : Nov 22  2012
# @Author  : Sharath Puranik
# @Version : 1

class RingBuffer:
	def __init__(self,size_max, count):
		self.max = size_max
		self.data = []
		self.cur = 0
		for i in range(self.max):
		    self.append(count)
	def append(self,x):
		"""append an element at the end of the buffer"""
		self.data.append(x)
		self.cur += 1
		if len(self.data) == self.max:
			self.cur=0
			self.__class__ = RingBufferFull
	def get(self):
  		""" return a list of elements from the oldest to the newest"""
		return self.data
	def get_curr(self):
	    return (self.cur-1) % self.max

class RingBufferFull:
	def __init__(self,n):
		raise "use RingBuffer to create objects, this class will automatically be alloted as the buffer is filled"
	def append(self,x):		
		self.data[self.cur]=x
		self.cur=(self.cur+1) % self.max
	def get(self):
		return self.data[self.cur:]+self.data[:self.cur]
	def get_curr(self):
	    return (self.cur-1) % self.max
