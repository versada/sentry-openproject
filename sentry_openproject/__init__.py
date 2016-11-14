# -*- coding: utf-8 -*-
"""
sentry_openproject
~~~~~~~~~~~~~~~~~~

:copyright: (c) 2016 by Naglis Jonaitis, HBEE
:license: BSD, see LICENSE for more details.
"""

try:
    VERSION = __import__('pkg_resources') \
        .get_distribution('sentry-openproject').version
except Exception as e:
    VERSION = 'unknown'
