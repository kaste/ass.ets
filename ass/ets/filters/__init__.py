import os
import hashlib
from useless.pipes import worker

import ass.ets 
import ass.ets.bundles

class FilterError(Exception): pass

@worker
def local_path(files, bundle):
	for file in files:
		yield os.path.join(bundle.map_from, file)


@worker
def remote_path(files, bundle):
	for file in files:
		if os.path.isabs(file):
			yield file
		else:
			yield '/'.join([bundle.map_to, file]) 

@worker
def translate_path(files, bundle):
	for file in files:
		relative_part = os.path.relpath(file, bundle.map_from)
		yield '/'.join([bundle.map_to, relative_part])

@worker
def relative_path(files, root):
	for file in files:
		yield os.path.relpath(file, root)

@worker
def echo(items, bundle):
	for item in items:
		yield item

@worker
def as_is(files, bundle):
	for file in files:
		if isinstance(file, ass.ets.Bundle):
			# handling nested bundles still feels hacky
			# assume the nested bundle yields relative paths with a root = subbundle.map_from
			# first localize, so we have an absolute path
			# then translate that path again to a relative path with the root = bundle.map_from
			for f in file.apply() | local_path(file) | relative_path(bundle.map_from):#translate_path(bundle):
				yield f
		else:
			yield file

@worker
def ask_manifest(files, bundle):
	# we need to consume the given iterator
	for file in files: pass

	for file in bundle.manifest.get(bundle.name):
		yield file

use_manifest = ask_manifest

@worker
def store_manifest(files, bundle):
	filenames = []
	for file in files:
		filenames.append(file)
		yield file

	bundle.manifest.set(bundle.name, filenames)
# @worker
# def compute_filename(files, bundle):
# 	for file in files: pass

# 	yield os.path.join(bundle.map_to, bundle.output)

@worker
def read(items, bundle):
	for item in items:
		if isinstance(item, ass.ets.Bundle):
			for content in item.apply():
				yield content
		else:
			filename = os.path.join(bundle.map_from, item)
			with open(filename) as file:
				yield file.read()


@worker
def merge(contents, bundle):
	rv = ''
	for content in contents:
		rv += content

	yield rv

# @consumer
# def _concat(files, bundle):
# 	rv = ''
# 	for file in files:
# 		rv += file

# 	return rv

def store_as(filename_):
	versioned = '%(version)s' in filename_

	@worker
	def store_as_(contents, bundle):
		# filename = os.path.join(bundle.map_from, filename_)
		
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


import subprocess

@worker
def uglifyjs(files, bundle):
	args = ['uglifyjs']
	for file in files:
		proc = subprocess.Popen(
			args,
			stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
			shell=True)
		stdout, stderr = proc.communicate(file)

		if proc.returncode != 0:
			raise FilterError(('uglifyjs: subprocess had error: stderr=%s, '+
                               'stdout=%s, returncode=%s') % (
                                    stderr, stdout, proc.returncode))

		yield stdout

@worker
def lessify(files, bundle):
	args = ['lessc', '-']
	for file in files:
		proc = subprocess.Popen(
			args,
			stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
			shell=True)
		stdout, stderr = proc.communicate(file)

		if proc.returncode != 0:
			raise FilterError(('lessc: subprocess had error: stderr=%s, '+
                               'stdout=%s, returncode=%s') % (
                                    stderr, stdout, proc.returncode))

		yield stdout

try:
	from cssminify import *
except ImportError:
	pass

def _get_pipe_for(ext, bundle):
	return ass.ets.bundles.Pipe( bundle.filters[ext][bundle.mode] )

@worker
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
