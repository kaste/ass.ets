import os
import hashlib

import ass.ets 
import ass.ets.bundles
from ass.ets.workers import filter, Incompatible

class FilterError(Exception): pass

@filter(accepts='filenames', yields='filenames')
def local_path(files, bundle):
	for file in files:
		yield os.path.join(bundle.map_from, file)


@filter(accepts='filenames', yields='filenames')
def remote_path(files, bundle):
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
def relative_path(files, root):
	for file in files:
		yield os.path.relpath(file, root)

@filter
def echo(items, bundle):
	for item in items:
		yield item

@filter(accepts='filenames', yields='filenames')
def as_is(files, bundle):
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
			for f in iterator | local_path(file) | relative_path(bundle.map_from):
				yield f
		else:
			yield file

@filter(yields='filenames')
def ask_manifest(files, bundle):
	# we need to consume the given iterator
	for file in files: pass

	for file in bundle.manifest.get(bundle.name):
		yield file

use_manifest = ask_manifest

@filter(accepts='filenames', yields='filenames')
def store_manifest(files, bundle):
	filenames = []
	for file in files:
		filenames.append(file)
		yield file

	bundle.manifest.set(bundle.name, filenames)

@filter(accepts='filenames', yields='contents')
def read(items, bundle):
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
	rv = ''
	for content in contents:
		rv += content

	yield rv

def store_as(filename_):
	versioned = '%(version)s' in filename_

	@filter(accepts='contents', yields='filenames')
	def store_as_(contents, bundle):
		for content in contents:
			filename = filename_
			if versioned:
				hash = hashlib.md5(content).hexdigest()[:8]
				filename = filename % dict(version=hash) 

			full_path = os.path.join(bundle.map_from, filename)
			with open(full_path, 'wb') as file:
				file.write(content)

			yield filename 

	return store_as_		

#

import subprocess
import sys
on_windows = sys.platform == 'win32'

@filter(accepts='contents', yields='contents')
def uglifyjs(files, bundle):
	args = ['uglifyjs']
	for file in files:
		proc = subprocess.Popen(
			args,
			stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
			shell=True if on_windows else False)
		stdout, stderr = proc.communicate(file)

		if proc.returncode != 0:
			raise FilterError(('uglifyjs: subprocess had error: stderr=%s, '+
                               'stdout=%s, returncode=%s') % (
                                    stderr, stdout, proc.returncode))

		yield stdout

@filter(accepts='contents', yields='contents')
def lessify(files, bundle):		
	args = ['lessc', '-']
	for file in files:
		proc = subprocess.Popen(
			args,
			stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
			shell=True if on_windows else False)
		stdout, stderr = proc.communicate(file)

		if proc.returncode != 0:
			raise FilterError(('lessc: subprocess had error: stderr=%s, '+
                               'stdout=%s, returncode=%s') % (
                                    stderr, stdout, proc.returncode))

		yield stdout

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
