#!/usr/bin/env python

from django.conf import settings
from django.conf.urls.defaults import include, patterns
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    (r'', include('activecalls.urls')),
    (r'', include('sirens.urls')),
    (r'^admin/', include(admin.site.urls)),

    # Should never be used in production, as nginx will serve these paths
    (r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
        { 'document_root': settings.STATIC_ROOT, 'show_indexes': True }),
)
