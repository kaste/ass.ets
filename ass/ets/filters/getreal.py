import subprocess
import sys
on_windows = sys.platform == 'win32'

from __init__ import FilterError
from ass.ets.workers import filter, Incompatible, discover_filters

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

@filter(accepts='contents', yields='contents')
def decaffeinate(files, bundle, bin='coffee', bare=False):
	args = [bin, '-sp' + 'b' if bare else '']
	return files | popens(bundle, args=args)


@filter(accepts='contents', yields='contents')
def cssminify(files, bundle):
	import cssmin

	for file in files:
		yield cssmin.cssmin(file)

minify = cssminify

__all__ = discover_filters(globals())
