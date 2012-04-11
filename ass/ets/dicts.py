

class listdicthybrid(object):
	"""Holds a list of objects. Provides some limited dict-like access."""
	
	def __init__(self, data=[], key_func=None):
		self.data = []
		self._key_func_ = key_func
		if isinstance(data, dict):
			self.update(data)
		else:
			self.extend(data)

	def extend(self, iter):
		for i in iter:
			self.append(i)

	def append(self, item):
		self.data.append( item )

	def update(self, d):
		for k, v in d.iteritems():
			self[k] = v

	def _index_of(self, key):
		for i, v in enumerate(self.data):
			if self._key_func_(v) == key:
				return i
		else:
			raise KeyError
		
	def __getitem__(self, key):
		try:
			i = self._index_of(key)
		except KeyError:
			raise
		return self.data[i]

	def __setitem__(self, key, bundle):
		try:
			i = self._index_of(key)
		except KeyError:
			return self.append( bundle )
		self.data[i] = bundle

	def __delitem__(self, key):
		try:
			i = self._index_of(key)
		except KeyError:
			raise IndexError
		self.data.pop(i)

	def __iter__(self):
		return iter(self.data)
		

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
	
