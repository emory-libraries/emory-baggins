import pkg_resources
import os

__version_info__ = (0, 5, 0, 'dev')


# Dot-connect all but the last. Last is dash-connected if not None.
__version__ = '.'.join([str(i) for i in __version_info__[:-1]])
if __version_info__[-1] is not None:
    __version__ += ('-%s' % (__version_info__[-1],))


# set package directory to allow referecing content and lookup
# files included in the source code and install package

if pkg_resources.resource_isdir(__name__, '.'):
    PACKAGE_DIR = pkg_resources.resource_filename(__name__, '.')
else:
    PACKAGE_DIR = os.path.dirname(__file__)
