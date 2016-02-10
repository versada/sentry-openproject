#!/usr/bin/env python
"""
sentry-openproject
==================

An extension for Sentry which integrates with OpenProject. Specifically, it
allows you to easily create new issues on OpenProject from events within
Sentry.

:copyright: (c) 2016 by HBEE, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from setuptools import setup, find_packages


install_requires = [
    'sentry>=8.0.0',
]

setup(
    name='sentry-openproject',
    version='0.1.0',
    author='Naglis Jonaitis',
    author_email='naglis@hbee.eu',
    url='http://github.com/HBEE/sentry-openproject',
    description='A Sentry extension which integrates with OpenProject.',
    long_description=__doc__,
    license='BSD',
    packages=find_packages(exclude=['tests']),
    zip_safe=False,
    install_requires=install_requires,
    test_suite='runtests.runtests',
    include_package_data=True,
    entry_points={
        'sentry.apps': [
            'openproject = sentry_openproject',
        ],
        'sentry.plugins': [
            'openproject = sentry_openproject.plugin:OpenProjectPlugin'
        ],
    },
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
)
