# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import base64

from requests.exceptions import HTTPError
from sentry.http import build_session
from sentry.utils import json

from .exceptions import ApiError


class OpenProjectClient(object):

    API_VERSION = 'v3'

    def __init__(self, url, apikey):
        self.url = url.rstrip('/')
        self.apikey = apikey

    def request(self, method, path, data=None, params=None):
        auth = base64.b64encode('apikey:%s' % self.apikey)
        headers = {
            'Authorization': 'Basic %s' % auth,
        }

        path = path.lstrip('/')
        session = build_session()
        try:
            resp = getattr(session, method.lower())(
                url='{}/api/{}/{}'.format(
                    self.url, OpenProjectClient.API_VERSION, path),
                headers=headers,
                json=data,
                params=params,
                allow_redirects=True,
            )
            resp.raise_for_status()
        except HTTPError as e:
            raise ApiError.from_response(e.response)
        return resp.json()

    def get_work_package(self, work_package_id):
        return self.request(
            'GET',
            'work_packages/{}'.format(work_package_id),
        )

    def create_work_package(self, project_id, title, work_package_type,
                            description=None, assignee_id=None, notify=True,
                            extra=None, **kwargs):
        data = {
            'subject': title,
            'description': {
                'format': 'textile',
                'raw': description,
            },
            '_links': {
                'type': {
                    'href': '/api/{}/types/{}'.format(
                        OpenProjectClient.API_VERSION, work_package_type),
                },
            },
        }
        if assignee_id:
            data['_links'].update({
                'assignee': {
                    'href': '/api/{}/users/{}'.format(
                        OpenProjectClient.API_VERSION, assignee_id)
                }
            })
        if extra:
            data.update(extra)
        return self.request(
            'POST',
            'projects/{}/work_packages'.format(project_id),
            data=data,
            params={'notify': 'true' if notify else 'false'},
        )

    def create_comment(self, work_package_id, comment, notify=True,
                       extra=None, **kwargs):
        data = {
            'comment': {
                'raw': comment,
            },
        }
        if extra:
            data.update(extra)
        return self.request(
            'POST',
            'work_packages/{}/activities/'.format(
                work_package_id,
            ),
            params={'notify': 'true' if notify else 'false'},
            data=data,
        )

    def list_assignees(self, project_id):
        return self.request(
            'GET',
            'projects/{}/available_assignees'.format(
                project_id),
        )

    def list_projects(self):
        return self.request('GET', 'projects')

    def list_project_types(self, project_id):
        return self.request(
            'GET',
            'projects/{}/types'.format(project_id),
        )

    def search_work_packages(self, project_id, query):
        return self.request(
            'GET',
            'projects/{}/work_packages'.format(project_id),
            params={
                'filters': json.dumps([
                    {
                        'subject': {
                            'operator': '~',
                            'values': [
                                query,
                            ],
                        },
                    },
                ]),
            },
        )
