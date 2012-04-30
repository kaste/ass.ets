The main purpose of an assets management application is to map local paths to urls on the server. Secondly you want to apply filters to sets of files, e.g. you want to merge and minify them. You often want this build-process to be automatic, on-the-fly, just by pressing refresh in your webbrowser. Later, in a production mode of your web application you just want to serve different, specific versions of your files.

Since I was just too dumb to use miracle2k's `webassets <https://github.com/miracle2k/webassets>`_ - did three days to write a new filter, new manifest implementation, then the ASSETS tag for jinja didn't liked my multiple environments - I put together this simple stuff.

In the following walk-through we use three external filters; you usually need `node <http://nodejs.org/>`_ with `uglifyjs <https://github.com/mishoo/UglifyJS>`_ and/or `lessc <http://lesscss.org>`_; to minify css the python package `cssmin <https://github.com/zacharyvoase/cssmin>`_ is used. You could also use `cleancss <https://github.com/GoalSmashers/clean-css>`_ and `coffeescript <http://coffeescript.org/>`_ . So you need to install some of these separately, but it's easy to write your own filters as you will see. Please contribute via `github <http://github.com/kaste/ass.ets>`_. 

::

	from ass.ets import *
	from ass.ets.filters import *

	import os
	here = os.path.dirname( os.path.realpath(__file__) )

	env = Environment(
		map_from=os.path.join(here, 'static'),
		map_to='/static',
		# t.i. a local file ./static/lib.js will later be served as /static/lib.js
		
		# use the default implementation of our manifest
		# we don't want the manifest in the static dir, so we provide an absolute path
		manifest=os.path.join(here, 'assets-manifest'),   
		#or provide your own object that answers get(key) and set(key, value)
		
		# in production mode we ask the manifest which file to serve, in this case 
		# we need to build at least once before we deploy
		production=use_manifest 
		#note: use_manifest is just another filter
	)

	jslib = bundle(
		"jquery.1.7.1.js", #...
		name='jslib',   # the naive manifest implementation uses this name as its key
		env=env,        # the bundle inherits all the settings from env 

		# very explicit chain of filters
		development=[read, merge, store_as('jslib.js')],
		build_=[read, merge, uglifyjs, store_as('jslib-%(version)s.js'), store_manifest],
		# yes ^ thats an underscore, because bundles have a build() method
		# uglifyjs assumes you have node's uglifyjs in your path, see below on how to cutomize this
	)

	# now we could do
	# env.mode = 'development'
	# print [url for url in jslib.urls()]

	# in our build script we do
	# env.mode = 'build_'
	# print [url for url in jslib.build()]

There's is no much difference between ``urls()`` and ``build()``. In the above example both pipes - 'development' and '\built_' - yield relative paths at the end, ``urls()`` just uses ``env.map_to`` to construct a url, where ``build()`` maps to the local path using ``map_from``.
Internally ``build()`` appends the following filter to the chain::

	@filter(accepts='filenames', yields='filenames')
	def local_path(files, bundle):
		for file in files:
			yield os.path.join(bundle.map_from, file)

Each ``@filter`` is effectively a ``worker`` from the `useless.pipes <http://pypi.python.org/pypi/useless.pipes>`_ package, which provides sugar for chaining generators. The filter-functions have a specific signature: the first argument always is the iterable from the previous filter. In case it's the first filter in the chain, it is the file-list you want to bundle. The second argument is the bundle we currently process. After that you may provide optional keyword arguments.

Ok, add another bundle::

	less_styles = Bundle(
		'styles.less', 
		name='less_style',
		env=env,
		development=as_is,
		build_=[read, merge, lessify]
	)
	all_styles = Bundle(
		less_styles, 'main.css',
		name='all_styles',
		env=env,
		development=as_is,
		build_=[read, merge, cssminify, store_as('styles-%(version)s.css'), store_manifest]
	)

T.i. in development mode we just spit the files as they are, when we build the less-file gets 'delessed', after that all css-files are merged and stored. Note that the `less_styles.build_` chain yields the css-content. We don't store a temporary file. The current implementation of `read` actually expects nested bundles to yield contents not filenames. 

Ok, now we need the less-js file in the development version of our app. We write a simple filter::

	def add(*filenames):
		@filter
		def add_(items, bundle):
			for item in items:
				yield item

			for filename in filenames:
				yield filename

		return add_			

	# and then
	less_styles = Bundle(
		'styles.less', 
		name='less_style',
		development=[as_is, add('less-1.2.1.min.js')],
		build_=[read, merge, lessify]
	)


	# all_styles.urls() now yields .css, .less and .js files in development mode and one .css file in built_ or production mode.

In jinja we could define two macros::

	{%- macro asset(url) %}
		{%- if url.endswith('.js') %}<script type="text/javascript" src="{{ url }}"></script>{%- endif %}
		{%- if url.endswith('.css') %}<link rel="stylesheet" type="text/css" href="{{ url }}" />{%- endif %}
		{%- if url.endswith('.less') %}<link rel="stylesheet/less" type="text/css" href="{{ url }}" />{%- endif %}
	{%- endmacro %}
	{%- macro assets_for(bundle) %}
		{%- for url in bundle.urls() %}
			{{ asset(url) }}
		{%- endfor %}
	{%- endmacro %}

Assume ``Flask`` and ``g.all_styles = all_styles``::

	{{ assets_for(g.all_styles) }}

and we're done.

Some last things; if you often write::
	
	[read, merge, uglifyjs, store_as('...'), store_manifest]

You could instead write something like this::

	# no magic here, just list + list
	process_js = [read, merge, uglifyjs]
	jslib.build_ = process_js + [store_as('...'), store_manifest]

OR::
	
	def process_js_and_store(fn):
		return [read, merge, uglifyjs, store_as(fn), store_manifest]
	jslib.build_ = process_js_and_store('...')

A filter that combines other filters by the way looks rather awkward, just to let you know::

	@filter
	def read_and_merge(items, bundle):
		return items | read(bundle) | merge(bundle)

As an example, some filters used herein::

	uglifyjs = popens(args=['uglifyjs'])
	lessify  = popens(args=['lessc', '-'])
	cleancss = popens(args=['cleancss'])

	def decaffeinate(bin='coffee', bare=False):
		args = [bin, '-sp' + 'b' if bare else '']
		return popens(args=args)

	# where popens is defined like

	@filter(accepts='contents', yields='contents')
	def popens(files, bundle, args=None, shell=True if on_windows else False, name=None):
		assert args is not None
		name = name or args[0] # assume we have a good name on the first argument which is the binary

		for file in files:
			proc = subprocess.Popen(
				args,
				stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
				shell=shell)
			stdout, stderr = proc.communicate(file)

			if proc.returncode != 0:
				raise FilterError(('%s: subprocess had error: stderr=%s, '+
	                               'stdout=%s, returncode=%s') % (
	                                    name, stderr, stdout, proc.returncode))

			yield stdout

Here, we use keyword arguments to 'customize' a filter. Say ``uglifyjs`` is not in your path, you could then redefine this filter::

	uglifyjs = popens(args=['C:\\....'], shell=False, name='uglify')	

Contribute back to `dev <http://github.com/kaste/ass.ets/tarball/master#egg=ass.ets-dev>`_ if you like.