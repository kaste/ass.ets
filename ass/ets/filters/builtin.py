import os
import hashlib
import urlparse

from __init__ import FilterError

import ass.ets 
import ass.ets.bundles
from ass.ets.workers import filter, Incompatible, discover_filters

@filter(accepts='filenames', yields='filenames')
def local_path(files, bundle):
	"""Expects relative paths and yields absolute paths using bundle.map_from."""
	for file in files:
		yield os.path.join(bundle.map_from, file)


@filter(accepts='filenames', yields='filenames')
def remote_path(files, bundle):
	"""Expects relative paths and yields urls by using bundle.map_to."""
	for file in files:
		# who needs this:
		# if os.path.isabs(file):
		# 	yield file
		# else:

		base = bundle.map_to
		base += '/' if base[-1:] != '/' else ''

		yield urlparse.urljoin(base, file) 

@filter(accepts='filenames', yields='filenames')
def translate_path(files, bundle):
	"""Given an absolute path, yields urls. 
	"""
	return files | relative_path(bundle) | remote_path(bundle)

@filter(accepts='filenames', yields='filenames')
def relative_path(files, bundle, root=None):
	"""Given an absolute path yields a relative one. By default uses
	bundle.map_from as the root.
	"""
	root = root or bundle.map_from

	for file in files:
		yield os.path.relpath(file, root)

@filter
def echo(items, bundle):
	for item in items:
		yield item

@filter(accepts='filenames bundles', yields='filenames')
def as_is(files, bundle):
	"""Just echoes filenames, but for nested bundles yields what they yield.
	"""
	for file in files:
		if isinstance(file, ass.ets.Bundle):
			nested_bundle = file
			iterator = nested_bundle.apply()
			if not iterator.yields('filenames'):
				raise Incompatible("%r must yield 'filenames', actually yields %r" % (nested_bundle, iterator.yields()))
			# handling nested bundles still feels hacky
			# assume the nested bundle yields relative paths with a root = subbundle.map_from
			# first localize, so we have an absolute path
			# then translate that path again to a relative path with the root = bundle.map_from
			for f in iterator | local_path(nested_bundle) | relative_path(bundle):
				yield f
		else:
			yield file

@filter(yields='filenames')
def ask_manifest(files, bundle, key=None):
	"""Assumes a Manifest on bundle.manifest which answers get(key). 
	By default the bundle's name is used as the key.
	Yields one or more local paths.
	"""
	# we need to consume the given iterator
	for file in files: pass

	key = key or bundle.name
	for file in bundle.manifest.get(key):
		yield file

use_manifest = ask_manifest

@filter(accepts='filenames', yields='filenames')
def store_manifest(files, bundle, key=None):
	"""Assumes a Manifest on bundle.manifest which answers set(key, value).
	By default the bundle's name is used as the key. The value is a 
	list of local paths.
	"""
	filenames = []
	for file in files:
		filenames.append(file)
		yield file

	key = key or bundle.name
	bundle.manifest.set(bundle.name, filenames)

@filter(accepts='filenames bundles', yields='contents')
def read(items, bundle):
	"""Reads the files and yields their contents. For nested bundles, just yields
	whatever they yield.  
	"""
	for item in items:
		if isinstance(item, ass.ets.Bundle):
			nested_bundle = item
			iterator = nested_bundle.apply()
			if not iterator.yields('contents'):
				raise Incompatible("%r must yield 'contents', actually yields %r" % (nested_bundle, iterator.yields()))
			for content in iterator:
				yield content
		else:
			filename = os.path.join(bundle.map_from, item)
			with open(filename) as file:
				yield file.read()


@filter(accepts='contents', yields='contents')
def merge(contents, bundle):
	"""Merge the contents of files. 

		['a', 'b'] | merge(bundle=None) == ['ab']


	"""
	yield ''.join(contents)

@filter(accepts='contents', yields='filenames')
def store(contents, bundle, name=None):
	"""Writes the given contents to disc. By default uses the name stored
	on bundle.output. 
	A '%(version)s' tag in the name gets replaced by hashing the content. 
	"""
	name = name or bundle.output
	versioned = '%(version)s' in name
	
	for content in contents:
		filename = name
		if versioned:
			hash = hashlib.md5(content).hexdigest()[:8]
			filename = filename % dict(version=hash) 

		full_path = os.path.join(bundle.map_from, filename)
		with open(full_path, 'wb') as file:
			file.write(content)

		yield filename 

def store_as(name):
	"""The same as calling store(name=name)"""
	return store(name=name)

import glob as glob_
@filter(accepts='filenames bundles', yields='filenames bundles')
def glob(files, bundle):
	for file in files:
		if isinstance(file, ass.ets.Bundle):
			yield file
		else:
			full_path = os.path.join(bundle.map_from, file)
			for expanded in glob_.iglob(full_path) | relative_path(bundle):
				yield expanded



# 

from ass.ets.dicts import ordered

def _get_pipe_for(ext, bundle):
	return ass.ets.bundles.Pipe( bundle.filters[ext][bundle.mode] )

@filter(accepts='filenames')
def automatic(files, bundle):
	"""Assumes a dict on bundle.filters, like so::

		env = Environment(
			filters={
				'js': {
					'development': [read, merge]
				},
				'css': {
					'development': [read, merge, minify]
				}
			}
		)
		bundle = Bundle(
			'jquery.js', 'styles.css',
			env=env,
			# partly overwrite the above defaults
			filters={ 'js': { 'development': [read, merge, uglifyjs] } },
			development=automatic
		)

	The automatic filter then chooses the correct filter chain by looking
	at the extension of the file.

	Alpha quality: Does not handle nested bundles.
	"""
	by_ext = ordered()
	for file in files:
		_, ext = os.path.splitext(file)
		ext = ext[1:]
		try:
			by_ext[ext].append(file)
		except KeyError:
			by_ext[ext] = [file]

	for ext, files in by_ext.iteritems():
		pipe = _get_pipe_for(ext, bundle)
		for thing in pipe.apply(files, bundle):
			yield thing


__all__ = discover_filters(globals()) + ['store_as',]