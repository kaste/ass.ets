import os
import hashlib

import ass.ets 
import ass.ets.bundles
from ass.ets.workers import filter, Incompatible, discover_filters

class FilterError(Exception): pass

@filter(accepts='filenames', yields='filenames')
def local_path(files, bundle):
	"""Expects relative paths and yields absolute paths using bundle.map_from."""
	for file in files:
		yield os.path.join(bundle.map_from, file)


@filter(accepts='filenames', yields='filenames')
def remote_path(files, bundle):
	"""Expects relative paths and yields urls by using bundle.map_to."""
	for file in files:
		if os.path.isabs(file):
			yield file
		else:
			yield '/'.join([bundle.map_to, file]) 

@filter(accepts='filenames', yields='filenames')
def translate_path(files, bundle):
	for file in files:
		relative_part = os.path.relpath(file, bundle.map_from)
		yield '/'.join([bundle.map_to, relative_part])

@filter(accepts='filenames', yields='filenames')
def relative_path(files, bundle, root=None):
	assert root is not None

	for file in files:
		yield os.path.relpath(file, root)

@filter
def echo(items, bundle):
	for item in items:
		yield item

@filter(accepts='filenames', yields='filenames')
def as_is(files, bundle):
	"""Just echoes filenames, but for nested bundles yields what they yield.
	"""
	for file in files:
		if isinstance(file, ass.ets.Bundle):
			bundle = file
			iterator = bundle.apply()
			if not iterator.yields('filenames'):
				raise Incompatible("%r must yield 'filenames', actually yields %r" % (bundle, iterator.yields()))
			# handling nested bundles still feels hacky
			# assume the nested bundle yields relative paths with a root = subbundle.map_from
			# first localize, so we have an absolute path
			# then translate that path again to a relative path with the root = bundle.map_from
			for f in iterator | local_path(file) | relative_path(bundle, root=bundle.map_from):
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

@filter(accepts='filenames', yields='contents')
def read(items, bundle):
	"""Reads the files and yields their contents. For nested bundles, just yields
	whatever they yield.  
	"""
	for item in items:
		if isinstance(item, ass.ets.Bundle):
			bundle = item
			iterator = bundle.apply()
			if not iterator.yields('contents'):
				raise Incompatible("%r must yield 'contents', actually yields %r" % (bundle, iterator.yields()))
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
	"""Writes the given contents to disc. You must provide a name. 
	A '%(version)s' tag in the name gets replaced by hashing the content. 
	"""
	assert name is not None
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


#

import subprocess
import sys
on_windows = sys.platform == 'win32'


@filter(accepts='contents', yields='contents')
def popens(files, bundle, args=None, shell=True if on_windows else False, name=None):
	"""Standard subprocess.Popen that expects a pipe on stdin and stdout.
	"""
	assert args is not None
	name = name or args[0] # assume we have a good name on the first argument which is the binary

	for content in files:
		proc = subprocess.Popen(
			args,
			stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
			shell=shell)
		stdout, stderr = proc.communicate(content)

		if proc.returncode != 0:
			raise FilterError(('%s: subprocess had error: stderr=%s, '+
                               'stdout=%s, returncode=%s') % (
                                    name, stderr, stdout, proc.returncode))

		yield stdout
	
uglifyjs = popens(args=['uglifyjs'])
lessify  = popens(args=['lessc', '-'])
cleancss = popens(args=['cleancss'])

def decaffeinate(bin='coffee', bare=False):
	args = [bin, '-sp' + 'b' if bare else '']
	return popens(args=args)


from cssminify import *				


#



def _get_pipe_for(ext, bundle):
	return ass.ets.bundles.Pipe( bundle.filters[ext][bundle.mode] )

@filter(accepts='filenames')
def automatic(files, bundle):
	by_ext = {}
	ordered = []
	for file in files:
		_, ext = os.path.splitext(file)
		ext = ext[1:]
		if not by_ext.has_key(ext):
			by_ext[ext] = []
			ordered.append(ext)
		by_ext[ext].append(file)

	for ext in ordered:
		files = by_ext[ext]
		pipe = _get_pipe_for(ext, bundle)
		for thing in pipe.apply(files, bundle):
			yield thing


__all__ = discover_filters(globals()) + ['store_as', 'decaffeinate']