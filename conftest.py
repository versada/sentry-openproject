from __future__ import absolute_import

from django.conf import settings

import os
import sys

# Run tests against sqlite for simplicity
os.environ.setdefault('DB', 'sqlite')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

pytest_plugins = ['sentry.utils.pytest']


def pytest_configure(config):
    settings.INSTALLED_APPS = tuple(settings.INSTALLED_APPS) + (
        'sentry_openproject',
    )
    from sentry.plugins import plugins
    from sentry_openproject.plugin import OpenProjectPlugin
    plugins.register(OpenProjectPlugin)
