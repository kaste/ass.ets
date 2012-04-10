

class ordered(object):
	"""Naive implementaion of an ordered dict."""
	def __init__(self, data={}):
		self.data = []
		self.update(data)

	def update(self, d):
		for k, v in d.items():
			self[k] = v

	def __getitem__(self, key):
		for k, v in self.data:
			if k == key:
				return v
		else:				
			raise KeyError

	def __setitem__(self, key, value):
		for i, (k, v) in enumerate(self.data):
			if k == key:
				self.data[i] = (key, value)
				break 
		else:
			self.data.append((key, value))

	def __delitem__(self, key):
		for i, (k, v) in enumerate(self.data):
			if k == key:
				self.data.pop(i)
				break
		else:
			raise IndexError

	def iterkeys(self):
		return (k for k, _ in self.data)

	def itervalues(self):
		return (v for _, v in self.data)

	def iteritems(self):
		return iter(self.data)

	def __iter__(self):
		return self.iterkeys()

class dotted(object):
	"""Naive mixin for a dict to enable attribute-style access."""
	__slots__ = ('data',)
	def __getattr__(self, key):
		return self.__getitem__(key)

	def __setattr__(self, key, value):
		if key in self.__class__.__slots__:
			object.__setattr__(self, key, value)
		else:
			self.__setitem__(key, value)

	def __delattr__(self, key):
		if key in self.__class__.__slots__:
			object.__delattr__(self, key)
		else:
			self.__delitem__(key)
	
