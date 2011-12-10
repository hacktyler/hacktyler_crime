#!/usr/bin/env python

from datetime import datetime, timedelta
import json
from uuid import uuid4

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
import pusher
from tastypie.serializers import Serializer

from activecalls.resources import ActiveCallResource
from activecalls.models import ActiveCall

def index(request):
    """
    Page shell for the client-side application.

    Bootstraps read-once data onto the page.
    """
    serializer = Serializer()
    resource = ActiveCallResource()

    since = datetime.now() - timedelta(hours=settings.DEFAULT_HOURS_DISPLAYED)
    calls = ActiveCall.objects.filter(reported__gt=since)

    bundles = [resource.build_bundle(obj=c) for c in calls]
    calls_bootstrap = [resource.full_dehydrate(b) for b in bundles]

    return render_to_response('index.html', {
        'settings': settings,
        'bootstrap_data': serializer.to_json({
            'active_calls': calls_bootstrap
        })
    })

@csrf_exempt
def pusher_user_auth(request):
    """
    Faux-authentication of users, for the purposes of counting them.
    """
    socket_id = request.POST['socket_id']
    channel_name = request.POST['channel_name']

    p = pusher.Pusher(
        app_id=settings.PUSHER_APP_ID,
        key=settings.PUSHER_KEY,
        secret=settings.PUSHER_SECRET,
        encoder=DjangoJSONEncoder
    )

    channel = p[channel_name]

    response = json.dumps(channel.authenticate(socket_id, { 'user_id': unicode(uuid4()) }), cls=DjangoJSONEncoder)

    return HttpResponse(response, status=200, content_type='application/json')

