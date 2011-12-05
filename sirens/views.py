#!/usr/bin/env python

from django.conf import settings
from django.shortcuts import render_to_response
#from tastypie.serializers import Serializer

#from activecalls.resources import ActiveCallResource
#from activecalls.models import ActiveCall

def index(request):
    """
    Page shell for the client-side application.

    Bootstraps read-once data onto the page.
    """
    #serializer = Serializer()
    #resource = ActiveCallResource()

    #calls = ActiveCall.objects.all()

    #bundles = [resource.build_bundle(obj=c) for c in calls]
    #calls_bootstrap = [resource.full_dehydrate(b) for b in bundles]

    return render_to_response('index.html', {
        'STATIC_URL': settings.STATIC_URL,
        #'bootstrap_data': serializer.to_json({
        #    'calls': calls_bootstrap
        #})
    })

