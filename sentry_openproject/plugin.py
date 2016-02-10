"""
sentry_openproject.plugin
~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2016 by HBEE, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""

import base64
import urlparse

from django import forms
from django.utils.translation import ugettext_lazy as _

from sentry import http
from sentry.utils import json
from sentry.utils.http import absolute_uri
from sentry.plugins.bases.issue import IssuePlugin

API_VERSION = 'v3'


class OpenProjectOptionsForm(forms.Form):
    host = forms.URLField(
        label=_('OpenProject Host URL'), initial='https://',
        widget=forms.TextInput(
            attrs={'class': 'span9', 'placeholder': 'eg. bugs.example.com'}
        ),
        help_text=_('The URL to your OpenProject instance')
    )
    apikey = forms.CharField(
        label=_('OpenProject API key'),
        widget=forms.TextInput(attrs={'class': 'span9'}),
        help_text=_(
            'API key of the OpenProject user, who will author new issues'
        ),
    )
    project_slug = forms.CharField(
        label=_('OpenProject Project Slug'),
        widget=forms.TextInput(attrs={'class': 'span9'}),
        help_text=_('Slug of the project on OpenProject'),
    )
    assignee_id = forms.IntegerField(
        label=_('OpenProject Assignee ID'),
        widget=forms.TextInput(attrs={'class': 'span9'}),
        required=False, min_value=1,
        help_text=_(
            'ID of the OpenProject user who will be the default assignee'),
    )

    def clean(self):
        config = self.cleaned_data
        if not all(config.get(k) for k in (
                'host', 'apikey', 'project_slug', 'assignee_id')):
            raise forms.ValidationError('Missing required configuration value')
        return config


class OpenProjectNewIssueForm(forms.Form):
    title = forms.CharField(
        max_length=200, widget=forms.TextInput(attrs={'class': 'span9'}))
    description = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'span9'}))


class OpenProjectPlugin(IssuePlugin):
    author = 'HBEE'
    author_url = 'https://github.com/HBEE/sentry-openproject'
    version = '0.1.1'
    description = (
        'Integrate OpenProject issue tracking by linking a user account '
        'to a project.')
    resource_links = [
        ('Bug Tracker', 'https://github.com/HBEE/sentry-openproject/issues'),
        ('Source', 'https://github.com/HBEE/sentry-openproject'),
    ]

    slug = 'openproject'
    title = _('OpenProject')
    conf_title = 'OpenProject'
    conf_key = 'openproject'
    project_conf_form = OpenProjectOptionsForm
    new_issue_form = OpenProjectNewIssueForm

    def is_configured(self, project, **kwargs):
        return all(
            (self.get_option(k, project) for k in (
                'host', 'apikey', 'project_slug', 'assignee_id')))

    def get_new_issue_title(self, **kwargs):
        return 'Create OpenProject Task'

    def get_initial_form_data(self, request, group, event, **kwargs):
        return {
            'title': 'Sentry:%s' % self._get_group_title(request, group, event),
            'description': self._get_group_description(request, group, event),
        }

    def _get_group_description(self, request, group, event):
        output = [
            absolute_uri(group.get_absolute_url()),
        ]
        body = self._get_group_body(request, group, event)
        if body:
            output.extend([
                '',
                '<pre>',
                body,
                '</pre>',
            ])
        return '\n'.join(output)

    def create_issue(self, group, form_data, **kwargs):
        """Create an issue on OpenProject"""
        host = self.get_option('host', group.project)
        apikey = self.get_option('apikey', group.project)
        project = self.get_option('project_slug', group.project)
        assignee = self.get_option('assignee_id', group.project)

        url = urlparse.urljoin(
            host, '/api/%s/projects/%s/work_packages' % (API_VERSION, project))
        auth = base64.b64encode('apikey:%s' % apikey)
        headers = {
            'Authorization': 'Basic %s' % auth,
            'Content-Type': 'application/json',
        }
        payload = {
            'subject': form_data['title'].encode('utf-8'),
            'description': {
                'format': 'textile',
                'raw': form_data['description'].encode('utf-8'),
            },
            '_links': {
            },
        }
        if assignee:
            payload['_links'].update({
                'assignee': {
                    'href': '/api/%s/users/%s' % (API_VERSION, assignee)
                }
            })

        session = http.build_session()
        r = session.post(url, data=json.dumps(payload), headers=headers)
        data = json.loads(r.text)

        if 'id' not in data:
            raise Exception('Unable to create OpenProject ticket')

        return data['id']

    def get_issue_url(self, group, issue_id, **kwargs):
        host = self.get_option('host', group.project)
        return urlparse.urljoin(host, '/work_packages/%s' % issue_id)
