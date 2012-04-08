import os
try:
	import yaml as serializer
except ImportError:
	import pickle as serializer

from options import Option, Options, Undefined, dict_getter
import filters as f

def manifest_setter(name):
	def setter(self, manifest):
		if isinstance(manifest, str):
			manifest = os.path.join(self.map_from, manifest)
			manifest = Manifest(manifest)

		self._options[name] = manifest

	return setter

class Manifest(object):
	def __init__(self, filename, serializer=serializer):
		self.filename = filename
		self.serializer = serializer
		self._manifest = None

	@property
	def manifest(self):
		if self._manifest is None:
			try:
				with open(self.filename) as f:
					self._manifest = serializer.load(f)
			except:
				self._manifest = {}
		return self._manifest

	def get(self, key):
		return self.manifest[key]

	def set(self, key, value):
		self.manifest[key] = value
		self._save_manifest()

	def _save_manifest(self):
		with open(self.filename, 'wb') as f:
			serializer.dump(self.manifest, f)



class Pipe(list):
	def __init__(self, seq):
		if not hasattr(seq, '__iter__'):
			seq = [seq]

		list.__init__(self, seq)


	def prepend(self, worker):
		self.insert(0, worker)

	def apply(self, iter, *a, **kw):
		_finally = kw.pop('_finally', list)

		p = iter
		for worker in self:
			p |= worker(*a, **kw)

		return (p | _finally) if _finally else p

class Environment(Options):
	map_from = Option()
	map_to = Option(default='/')
	mode = Option()
	manifest = Option(setter=manifest_setter)
	filters = Option(getter=dict_getter)

	# because of the options-inheritance we define these here, even though
	# we might only need them way down for the bundles
	production = Option()
	development = Option()#getter=pipelize_getter)
	build_ = Option()

class Assets(Environment):
	def __init__(self, env=None, **kw):
		self.env = env
		if env is not None:
			self.parent = env

class Bundle(Assets):
	name = Option()

	def __init__(self, files=[], **kw):
		super(Bundle, self).__init__(**kw)
		self.files = files

	def urls(self, urlize=f.remote_path):
		return self.apply(append=urlize)

		# pipe = getattr(self, self.mode)
		# pipe.append(urlize)
		# return self.apply(pipe=pipe)
		# return pipe.apply(self.files, self)

		# if pipe in (as_is, use_manifest):
		# 	pipe = [pipe]

		# pipe.append(urlize)
		# return self.apply(pipe=pipe)

	def apply(self, mode=None, pipe=None, append=None):
		pipe = Pipe( pipe or getattr(self, mode or self.mode) )
		if append:
			pipe.append(append)
		# pipe = isinstance(pipe, Pipe) and pipe or \
		# 	   (pipe and Pipe(pipe)) or \
		# 	   getattr(self, mode or self.mode)

		return pipe.apply(self.files, self)

		# p = input or self.files 
		# for worker in pipe:
		# 	p |= worker(self)

		# return p | list 

	def build(self, mode='build_', localize=f.local_path):
		return self.apply(mode=mode, append=localize)

		# pipe = getattr(self, mode)
		# pipe.append(localize)
		# return self.apply(pipe=pipe)

		# content = self.apply() | local_path(self) 
		# hash = hashlib.md5(content).hexdigest()[:8]
		# filename = (self.output % hash) if '%s' in self.output else self.output
		# filename = os.path.join(self.map_from, filename)

		# with open(filename, 'wb') as f:
		# 	f.write(content)

		return content

