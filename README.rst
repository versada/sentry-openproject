sentry-openproject
==================

An extension for Sentry which integrates with OpenProject. Specifically, it
allows you to easily create new issues on OpenProject from events within
Sentry.


Install
-------

Install the package via ``pip``::

    pip install sentry_openproject


Configuration
-------------

Create a new Sentry user within your OpenProject instance. This user will
be creating tickets on your behalf via Sentry.

Go to your project's configuration page (Projects -> [Project]) and select the
Settings tab. In the left Settings pane select All Integrations, enable
the OpenProject plugin and click Save Changes. A new entry will appear in
the left Settings pane. Click on it and set the OpenProject integratation
details. The first three options (OpenProject Host URL, OpenProject API key and
OpenProject Project Slug) are required. Once done, click Save Changes.

You'll now see a new action `Create OpenProject Task` in the More menu on new
issues.

