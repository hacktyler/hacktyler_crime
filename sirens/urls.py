#!/usr/bin/env python

from django.conf.urls.defaults import patterns, url

from sirens import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^pusher/auth$', views.pusher_user_auth, name='pusher_user_auth')
)

