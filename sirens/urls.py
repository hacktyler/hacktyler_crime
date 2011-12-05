#!/usr/bin/env python

from django.conf.urls.defaults import patterns, url

from sirens import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index')
)

