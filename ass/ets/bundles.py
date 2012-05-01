import os, warnings, operator

try:
	import yaml as serializer
except ImportError:
	import pickle as serializer

from options import Option, Options, dict_getter
import filters as f
import dicts

def manifest_setter(name):
	def setter(self, manifest):
		if isinstance(manifest, str):
			manifest = os.path.join(self.map_from, manifest)
			manifest = Manifest(manifest)

		self._options[name] = manifest

	return setter

class Manifest(object):
	"""Naive implementation. Uses yaml or pickle to serialize.

	"""
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

			
class CommonOptions(Options):
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

	def __init__(self, env=None, **kw):
		if env is not None:
			self.env = env

	@property
	def parent(self):
		return self.env


class bundleslist(dicts.listdicthybrid, dicts.dotted):
	__slots__ = ('data', '_env', '_key_func_')

	def __init__(self, data=[], env=None):
		self._env = env
		super(bundleslist, self).__init__(data, key_func=lambda i: getattr(i, 'name', None))

	def _prepare_bundle(self, bundle, key):
		if key is not None:
			try:
				getattr(bundle, 'name')
			except:
				bundle.name = key
		try:
			getattr(bundle, 'env')
		except:
			bundle.env = self._env

	def append(self, item):
		self._prepare_bundle(item, None)
		super(bundleslist, self).append(item)

	def __setitem__(self, key, value):
		self._prepare_bundle(value, key)
		super(bundleslist, self).__setitem__(key, value)

class assetslist(bundleslist):
	#assets can be either just a path or a bundle 
	def _prepare_bundle(self, bundle, key):
		if not isinstance(bundle, Bundle):
			return
		super(assetslist, self)._prepare_bundle(bundle, key)

	def _index_of(self, key):
		for i, v in enumerate(self.data):
			try:
				if self._key_func_(v) == key:
					return i
			except AttributeError:
				pass
		else:
			raise KeyError

class Pipe(list):
    def __init__(self, seq):
        if not hasattr(seq, '__iter__'):
            seq = [seq]

        list.__init__(self, seq)

    def accepts(self, symbol=None):
        return self[0].accepts(symbol)

    def yields(self, symbol=None):
        return self[-1].yields(symbol)

    def prepend(self, worker):
        self.insert(0, worker)

    def apply(self, iter, *a, **kw):
        p = iter
        for worker in self:
            p |= worker(*a, **kw)

        return p

class Environment(CommonOptions): 
	"""An Environment is just a configuration object. Consider:

		env = Environment(map_from='./static')
		js = bundle(env=env)

		js.map_from == './static'


	"""

class Assets(CommonOptions):
	"""An Assets-instance is a container for bundles. The
	name is probably confusing.

		assets = Assets(
			bundle(name='bundleA', assets=['fileA'...] ...),
			production=use_manifest, #etc
		)

		# now you could:
		for bundle in assets: ....
			bundle.build()

		# or access the named bundle, just like
		assets.bundles.bundleA.build()

		# or assign a bundle
		assets.bundles.javascripts = bundle(...)

	Notice, that the name of the bundle, t.i. its name-attribute, gets
	used as the key for the bundles-mapping.

	"""
	def __init__(self, *bundles, **kw):
		super(Assets, self).__init__(**kw)
		if not bundles and kw.has_key('bundles'):
			bundles = kw['bundles']
		self.bundles = bundles

	@property
	def bundles(self):
		return self._bundles

	@bundles.setter
	def bundles(self, new_value):
		if not isinstance(new_value, bundleslist):
			new_value = bundleslist(new_value, env=self)
		self._bundles = new_value

	def __iter__(self):
		return self.bundles.itervalues()

	def __repr__(self):
		return "Assets(%s)" % ', '.join(map(lambda i: "%r" % i, self.bundles.values()))


class Bundle(CommonOptions):
	"""A Bundle bundles files or nested bundles. Named bundles
	can be accessed via the assets member.

		less_style = bundle(name=less)
		styles = bundle(
			less_style, 'main.css', #...
		)

		styles.assets.less == less_style
		styles.assets['less'] == less_style

	Bundles provide the two useful methods urls() and build() and
	the underlying method apply().

	Usually you set the mode and call urls() and or build()

		styles.make_it = [read, merge] #...
		styles.mode = 'make_it'
		styles.build()

	But better start with the mode names 'development', 'production' 
	and 'build_'.


	"""
	name = Option()
	output = Option()

	def __init__(self, *assets, **kw):
		super(Bundle, self).__init__(**kw)
		if not assets and kw.has_key('assets'):
			assets = kw['assets']
		self.assets = assets

	@property
	def assets(self):
		return self._assets

	@assets.setter
	def assets(self, new_value):
		if not isinstance(new_value, assetslist):
			new_value = assetslist(new_value, env=self)
		self._assets = new_value



	def urls(self, urlize=f.remote_path):
		"""Applies the mode self.mode, converts paths to urls.
		
		Actually returns a generator you have to consume.

		"""
		return self.apply(append=urlize)

	def apply(self, mode=None, pipe=None, append=None):
		"""Either provide a list of workers/filters on pipe or
		a name of a mode, otherwise uses self.mode.

		Actually not necessarily applies the filters but returns
		a generator you have to consume.  
		"""
		pipe = Pipe( pipe or getattr(self, mode or self.mode) )
		if append:
			pipe.append(append)

		return pipe.apply(self.assets, self)

	def build(self, mode=None, localize=f.local_path):
		"""Applies the set mode, converts relative paths to absolute 
		local paths and returns a list.

		"""
		if mode:
			warnings.warn('Because of the way nested bundles are built, passing a mode to build() might not work as you might expect.')

		return self.apply(mode=mode, append=localize) | list

	def __repr__(self):
		try:
			return "Bundle(name=%r)" % self.name
		except:
			return "Bundle(%s)" % ', '.join(map(lambda i: "%r" % i, self.assets.values()))


bundle = Bundle