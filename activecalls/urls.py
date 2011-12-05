#!/usr/bin/env python

from django.conf.urls.defaults import include, patterns
from tastypie.api import Api

from activecalls.resources import ActiveCallResource

api_1_0 = Api(api_name='1.0')
api_1_0.register(ActiveCallResource())

urlpatterns = patterns('',
    (r'^api/', include(api_1_0.urls)),
)

