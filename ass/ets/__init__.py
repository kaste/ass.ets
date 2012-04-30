"""
    ass.ets
    
    Asset management for webapps.

    :copyright: (c) 2012 by Herrn Kaste <herr.kaste@gmail.com>.
    :license: BSD, see LICENSE for more details.
"""

__version__ = "0.0.6"

from bundles import Environment, Assets, bundle, Bundle, Manifest
import filters as f
from options import Option, Options, dict_getter
from ass.ets.workers import worker, filter, Incompatible

