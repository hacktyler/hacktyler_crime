#!/usr/bin/env python

from django.contrib.gis.db.models import GeometryField
from tastypie.fields import CharField
from tastypie.resources import ModelResource

from activecalls.fields import GeometryApiField
from activecalls.models import ActiveCall

class GeometryResource(ModelResource):
    @classmethod
    def api_field_from_django_field(cls, f, default=CharField):
        if isinstance(f, GeometryField):
            return GeometryApiField
    
        return super(GeometryResource, cls).api_field_from_django_field(f, default)

class ActiveCallResource(GeometryResource):
    class Meta:
        queryset = ActiveCall.objects.all()
        resource_name = 'active_call'
        allowed_methods = ['get']

        excludes = ['raw_html']

