# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from exam import fixture
from django.test import RequestFactory
from sentry.testutils import PluginTestCase

from sentry_openproject.plugin import OpenProjectPlugin


class OpenProjectPluginTest(PluginTestCase):

    @fixture
    def plugin(self):
        return OpenProjectPlugin()

    @fixture
    def request(self):
        return RequestFactory()

    def test_conf_key(self):
        assert self.plugin.conf_key == 'openproject'

    def test_entry_point(self):
        self.assertAppInstalled('openproject', 'sentry_openproject')
        self.assertPluginInstalled('openproject', self.plugin)

    def test_get_issue_label(self):
        group = self.create_group(message='Hello world', culprit='foo.bar')
        assert self.plugin.get_issue_label(group, 1) == 'WP#1'

    def test_get_issue_url(self):
        self.plugin.set_option('url', 'https://example.com', self.project)
        self.plugin.set_option('project_slug', 'foo', self.project)
        group = self.create_group(message='Hello world', culprit='foo.bar')
        assert (
            self.plugin.get_issue_url(group, 1) ==
            'https://example.com/work_packages/1'
        )

    def test_is_configured(self):
        assert self.plugin.is_configured(None, self.project) is False
        self.plugin.set_option('url', 'https://example.com', self.project)
        self.plugin.set_option('apikey', '1234567890abcdef', self.project)
        self.plugin.set_option('project_slug', 'foo', self.project)
        assert self.plugin.is_configured(None, self.project) is True
