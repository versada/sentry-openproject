# -*- coding: utf-8 -*-
"""
sentry_openproject.plugin
~~~~~~~~~~~~~~~~~~~~~~~~~

:copyright: (c) 2016 by HBEE, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import, unicode_literals

import urlparse

import six

from rest_framework.response import Response
from sentry.exceptions import PluginError
from sentry.plugins.bases.issue2 import IssueGroupActionEndpoint, IssuePlugin2
from sentry.utils.http import absolute_uri

from .client import OpenProjectClient
from .exceptions import ApiError, ApiUnauthorized
from .utils import get_secret_field_config

ERR_INTERNAL = (
    'An internal error occurred within the OpenProject plugin'
)

ERR_UNAUTHORIZED = (
    'Unauthorized: either your API token is invalid or you do not have access'
)

ERR_404 = (
    'OpenProject returned a 404 Not Found error. If such project exists, '
    'ensure the API token user has access to it.'
)


class OpenProjectPlugin(IssuePlugin2):
    title = 'OpenProject'
    slug = 'openproject'
    description = 'Integrate OpenProject issue tracking by projects'
    conf_title = title
    conf_key = 'openproject'

    author = 'HBEE'
    author_url = 'https://github.com/HBEE/sentry-openproject'
    version = '0.2.0'
    resource_links = [
        ('Bug Tracker', 'https://github.com/HBEE/sentry-openproject/issues'),
        ('Source', 'https://github.com/HBEE/sentry-openproject'),
    ]

    def get_group_urls(self):
        return super(OpenProjectPlugin, self).get_group_urls() + [
            (r'^autocomplete', IssueGroupActionEndpoint.as_view(
                view_method_name='view_autocomplete',
                plugin=self,
            )),
        ]

    def is_configured(self, request, project, **kwargs):
        return all(
            (self.get_option(k, project)
             for k in ('url', 'apikey', 'project_slug'))
        )

    def get_group_description(self, request, group, event):
        '''Override of the function in parent class.

        Wraps exception body with <pre> tag to allow it to be parsed
        by Textile.
        '''
        output = [
            absolute_uri(group.get_absolute_url()),
        ]
        body = self.get_group_body(request, group, event)
        if body:
            output.extend([
                '',
                '<pre>',
                body,
                '</pre>',
            ])
        return '\n'.join(output)

    def get_new_issue_fields(self, request, group, event, **kwargs):
        fields = super(OpenProjectPlugin, self).get_new_issue_fields(
            request, group, event, **kwargs)
        allowed_types = self.get_allowed_types(request, group)
        return [{
            'name': 'project_slug',
            'label': 'OpenProject Project Slug',
            'default': self.get_option('project_slug', group.project),
            'type': 'text',
            'readonly': True
        }] + fields + [
            {
                'name': 'type',
                'label': 'Work Package Type',
                'default': allowed_types[0][0],
                'type': 'select',
                'required': True,
                'choices': allowed_types,
            },
            {
                'name': 'assignee',
                'label': 'Assignee',
                'default': '',
                'type': 'select',
                'required': False,
                'choices': self.get_allowed_assignees(request, group)
            },
        ]

    def get_link_existing_issue_fields(self, request, group, event, **kwargs):
        return [{
            'name': 'issue_id',
            'label': 'Work Package',
            'default': '',
            'type': 'select',
            'has_autocomplete': True,
        }, {
            'name': 'comment',
            'label': 'Comment',
            'default': absolute_uri(group.get_absolute_url()),
            'type': 'textarea',
            'help': ('Leave blank if you don\'t want to '
                     'add a comment to the OpenProject work package.'),
            'required': False
        }]

    def get_issue_label(self, group, issue_id, **kwargs):
        return 'WP#%s' % issue_id

    def get_issue_url(self, group, issue_id, **kwargs):
        url = self.get_option('url', group.project)
        return urlparse.urljoin(url, '/work_packages/{}'.format(issue_id))

    def get_client(self, project, user):
        url = self.get_option('url', project)
        apikey = self.get_option('apikey', project)
        if not all((url, apikey)):
            raise PluginError('OpenProject plugin not correctly configured!')
        return OpenProjectClient(url, apikey)

    def create_issue(self, request, group, form_data, **kwargs):
        client = self.get_client(group.project, request.user)
        try:
            response = client.create_work_package(
                self.get_option('project_slug', group.project),
                form_data['title'],
                form_data['type'],
                description=form_data.get('description'),
                assignee_id=form_data.get('assignee'),
            )
        except Exception as e:
            self.raise_error(e)

        return response['id']

    def link_issue(self, request, group, form_data, **kwargs):
        client = self.get_client(group.project, request.user)
        try:
            issue = client.get_work_package(form_data['issue_id'])
        except Exception as e:
            self.raise_error(e)

        comment = form_data.get('comment')
        if comment:
            try:
                client.create_comment(issue['id'], comment)
            except Exception as e:
                self.raise_error(e)

        return {
            'title': issue['subject'],
        }

    def get_configure_plugin_fields(self, request, project, **kwargs):
        apikey = self.get_option('apikey', project)
        apikey_field = get_secret_field_config(
            apikey,
            'This is API key of an OpenProject user, who will be the author '
            'of the issue on OpenProject.',
            include_prefix=True,
        )
        apikey_field.update({
            'name': 'apikey',
            'label': 'OpenProject API key',
            'placeholder': 'e.g. 0123456789abcdef0123456789abcdef01234567',
        })
        return [
            {
                'name': 'url',
                'label': 'OpenProject URL',
                'default': self.get_option('url', project),
                'type': 'text',
                'placeholder': 'e.g. https://openproject.example.com',
                'help': 'The URL to your OpenProject instance.',
            },
            apikey_field,
            {
                'name': 'project_slug',
                'label': 'Project Slug',
                'default': self.get_option('project_slug', project),
                'type': 'text',
                'placeholder': 'e.g. example-project',
                'help': ('This should be the project slug of this project on '
                         'OpenProject.'),
            },
        ]

    def get_allowed_assignees(self, request, group):
        client = self.get_client(group.project, request.user)
        try:
            response = client.list_assignees(
                project_id=self.get_option('project_slug', group.project),
            )
        except Exception as e:
            self.raise_error(e)

        users = tuple(
            (u['id'], '{firstName} {lastName}'.format(**u))
            for u in response.get('_embedded', {}).get('elements', [])
        )

        return (('', 'Unassigned'),) + users

    def get_allowed_types(self, request, group):
        client = self.get_client(group.project, request.user)
        try:
            response = client.list_project_types(
                project_id=self.get_option('project_slug', group.project),
            )
        except Exception as e:
            self.raise_error(e)

        return tuple(
            (u['id'], u['name'])
            for u in response.get('_embedded', {}).get('elements', [])
        )

    def message_from_error(self, exc):
        if isinstance(exc, ApiUnauthorized):
            return ERR_UNAUTHORIZED
        elif isinstance(exc, ApiError):
            if exc.code == 404:
                return ERR_404
            return ('Error Communicating with OpenProject (HTTP %s): %s' % (
                exc.code,
                exc.json.get('message', 'unknown error')
                if exc.json else 'unknown error',
            ))
        else:
            return ERR_INTERNAL

    def raise_error(self, exc):
        if isinstance(exc, ApiError):
            raise PluginError(self.message_from_error(exc))
        elif isinstance(exc, PluginError):
            raise
        else:
            self.logger.exception(six.text_type(exc))
            raise PluginError(self.message_from_error(exc))

    def view_autocomplete(self, request, group, **kwargs):
        field = request.GET.get('autocomplete_field')
        query = request.GET.get('autocomplete_query')
        if not field == 'issue_id' or not query:
            return Response({'issue_id': []})

        project_slug = self.get_option('project_slug', group.project)
        client = self.get_client(group.project, request.user)

        try:
            response = client.search_work_packages(
                project_slug, query.encode('utf-8')
            )
        except Exception as e:
            return Response({
                'error_type': 'validation',
                'errors': [{'__all__': self.message_from_error(e)}]
            }, status=400)

        issues = [{
            'text': '(#{id}) {subject}'.format(**i),
            'id': i['id'],
        } for i in response.get('_embedded', {}).get('elements', [])]

        return Response({field: issues})
