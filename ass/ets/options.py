
class option_property(property): pass

def option(name, desc='', getter=None, setter=None, default=None):
	def get(self):
		try:
			return self._options[name]
		except KeyError:
			try:
				return getattr(self.parent, name)
			except AttributeError:
				if default:
					return default

				raise AttributeError("%r is undefined" % name)

	def set(self, value):
		self._options[name] = value

	def del_(self):
		self._options.pop(name)

	# print setter, set, setter or set
	return option_property(getter and getter(name, default) or get, 
					setter and setter(name) or set, 
					del_, desc)

def pipelize_getter(name, default=None):
	def getter(self):
		try:
			rv = self._options[name]
		except KeyError:
			try:
				rv = getattr(self.parent, name)
			except AttributeError:
				if default:
					rv = default

				raise AttributeError("%s is undefined." % name)

		return Pipe(rv)

	return getter



def dict_getter(name, default=None):

	def _update(parent, this):
		for k, v in this.iteritems():
			if parent.has_key(k) and isinstance(v, dict):
				_update(parent[k], v)
			else:
				parent[k] = v
		
	def getter(self):
		this = self._options.get(name, default or {})
		parent = getattr( getattr(self, 'parent', None), name, {}).copy()

		if not parent and not this:	
			raise Undefined("%s is undefined." % name)

		_update(parent, this)

		return parent

	return getter



class Option(object):
	def __init__(self, name=None, **kw):
		self.name = name
		self.kw = kw

	def get_property(self):
		return option(self.name, **self.kw)

# we inject this as a @property at self._options
def _get_options_(self):
	try:
		return self.__options
	except AttributeError:
		self.__options = dict()
		return self.__options

class InjectOptions(type):
	"""Puts a dict on self._options and a option-property for each defined Option"""
	def __init__(cls, name, bases, dict_):
		super(InjectOptions, cls).__init__(name, bases, dict_)
		setattr(cls, '_options', property(_get_options_))

		for key, option in dict_.iteritems():
			if isinstance(option, Option):
				if option.name is None:
					option.name = key
				setattr(cls, option.name, option.get_property())

class Options(object):
	__metaclass__ = InjectOptions

	def __new__(cls, *a, **kw):
		instance = super(Options, cls).__new__(cls)

		for key, value in kw.iteritems():
			varname = getattr(cls, key, None)
			if isinstance(varname, option_property):
				setattr(instance, key, value)

		return instance

